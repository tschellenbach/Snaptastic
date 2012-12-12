import logging
import os
from time import sleep
from datetime import timedelta, datetime

from boto.utils import get_instance_metadata

from snaptastic import exceptions
from snaptastic import get_ec2_conn
from snaptastic import metaclass
from snaptastic.ebs_volume import EBSVolume
from snaptastic.utils import get_userdata_dict, add_tags


logger = logging.getLogger(__name__)


class Snapshotter(object):
    '''
    Reusable class for creating snapshots and mounting them on boot

    This class makes a few assumptions:
    - role
    - cluster
    - environment
    Are part of your userdata

    The key things to customize:
    - get_volumes
    These hooks
    - pre_mounts, post_mounts
    - pre_snapshots, post_snapshots
    '''
    SNAPSHOT_EXPIRY_DAYS = 7
    name = None

    __metaclass__ = metaclass.SnapshotterRegisteringMetaClass

    def __init__(self, userdata=None, metadata=None, connection=None, bdm=None):
        '''
        Goes through the steps needed to mount the specified volume
        - checks if we have a snapshot
        - create a new volume and attach it
        - tag the volume
        - load the data from the snapshot into the volume

        :param userdata: dictionary with the userdata
        :type userdata: dict
        :param metadata: metadata for the instance
        :type metadata: dict
        :param connection: boto connection object
        :param bdm: dictionary describing the device mapping

        '''
        self.userdata = get_userdata_dict() if userdata is None else userdata
        self.metadata = get_instance_metadata(
        ) if metadata is None else metadata
        self.con = get_ec2_conn() if connection is None else connection
        self.bdm = self.get_bdm() if bdm is None else bdm

    '''
    These you will need to customize
    '''

    def get_volumes(self):
        '''
        Get the volumes for this instance, customize this at will
        '''
        volume = EBSVolume(device='/dev/sdf', mount_point='/mnt/test', size=5)
        volumes = [volume]
        return volumes

    def get_filter_tags(self):
        '''
        The tags which are used for finding the correct snapshot to load from.
        In addition to these tags, mount point is also always added.

        Use these to unique identify different parts of your infrastructure
        '''
        tags = {
            'role': self.userdata['role'],
            'cluster': self.userdata['cluster'],
            'environment': self.userdata['environment']
        }
        return tags

    '''
    Main functions to call when using Snapshotter
    '''

    def make_snapshots(self, volumes=None):
        '''
        Make snapshots of all the volumes
        '''
        snapshots = []
        volumes = volumes or self.get_volumes()
        logger.info('making snapshots of %s volumes', len(volumes))
        #hook for customizing the behaviour before snapshots
        self.pre_snapshots(volumes)
        for vol in volumes:
            self.pre_snapshot(vol)
            snapshot = self.make_snapshot(vol)
            snapshots.append(snapshot)
            self.post_snapshot(vol)
        #hook for customizing the behavior after snapshots
        self.post_snapshots(volumes)
        return snapshots

    def make_snapshot(self, vol):
        #get a snapshot name
        description = self.get_snapshot_description(vol)
        logger.info(
            'preparing to create a snapshot with description %s', description)
        # find the volume ID for this device
        volume_id = self.get_volume_id(vol)
        #get the tags, note that these are used for finding the right snapshot
        tags = self.get_tags_for_volume(vol)
        #Don't freeze more than we need to
        with vol.freeze():
            logger.info('creating snapshot')
            snapshot = self.con.create_snapshot(
                volume_id, description=description)
            logger.info('succesfully created snapshot with id %s', snapshot.id)
        #Add tags
        logger.info('tagging snapshot %s with tags %s', snapshot.id, tags)
        add_tags(snapshot, tags)
        return snapshot

    def mount_snapshots(self, volumes=None, ignore_mounted=False):
        ''' Loops through the volumes and runs mount_volume on them

        When ignore_mounted is True it will ignore DeviceAlreadyExists errors
        '''
        volumes = volumes or self.get_volumes()
        logger.info('preparing to mount %s volumes', len(volumes))
        self.pre_mounts(volumes)
        for vol in volumes:
            self.pre_mount(vol)
            try:
                self.mount_snapshot(vol)
            except exceptions.DeviceAlreadyExists:
                if ignore_mounted:
                    logger.info("Ignoring {}".format(vol))
                else:
                    raise

            self.post_mount(vol)

        self.post_mounts(volumes)

        return volumes

    def mount_snapshot(self, ebs_volume):
        '''
        Goes through the steps needed to mount the specified volume
        - checks if we have a snapshot
        - create a new volume and attach it
        - tag the volume
        - load the data from the snapshot into the volume

        :param ebs_volume: the volume specification, we're mounting
        :type ebs_volume: EBSVolume
        '''
        #see if we have a snapshot we can start from
        try:
            snapshot_id = self.get_snapshot(ebs_volume)
        except exceptions.MissingSnapshot, e:
            snapshot_id = None
        logger.info('mounting a volume to %s with snapshot %s',
                    ebs_volume.mount_point, snapshot_id)

        #create the device and attach
        boto_volume = self.create_volume(ebs_volume, snapshot_id=snapshot_id)
        #attach the volume to the instance
        self.attach_volume(ebs_volume, boto_volume)
        # if it's not from a snapshot we need to format
        if snapshot_id is None:
            ebs_volume.format()

        #mount the volume
        ebs_volume.mount()

    def unmount_snapshots(self, volumes=None):
        '''
        Unmounting the volumes, mainly for testing
        '''
        volumes = volumes or self.get_volumes()
        self.pre_unmounts(volumes)
        logger.info('unmounting volumes %s', volumes)
        for vol in volumes:
            #first unmount
            self.pre_unmount(vol)
            try:
                vol.unmount()
            except exceptions.UnmountException, e:
                logger.warn(e)
            try:
                #now detach
                volume_id = self.get_volume_id(vol)
                self.detach_volume(vol, volume_id)
            except Exception, e:
                logger.warn(e)
            self.post_unmount(vol)
        self.post_unmounts(volumes)
        return volumes

    '''
    Volume related functionality
    '''

    def create_volume(self, vol, snapshot_id=None):
        '''
        Creates a volume and attaches it to this instance

        If given a snapshot id, populates from the snapshot, else
        formats the volume first

        Subsequently mounts the volume to the given mount point
        '''
        #catch this at a higher level if we want to skip
        if os.path.exists(vol.instance_device):
            error_message = 'Device %s already exists' % vol.instance_device
            raise exceptions.DeviceAlreadyExists(error_message)

        # we always create a new volume when mounting upon boot
        # load from a snapshot if we have one
        log_message = 'Creating a volume of size %s in zone %s from snapshot %s'
        logger.info(log_message, vol.size, self.availability_zone, snapshot_id)
        boto_volume = self.con.create_volume(size=vol.size,
                                             zone=self.availability_zone,
                                             snapshot=snapshot_id
                                             )
        # tag the volume
        tags = self.get_tags_for_volume(vol)
        logger.info('tagging volume %s with tags %s', boto_volume.id, tags)
        add_tags(boto_volume, tags)
        logger.info('tags added succesfully')

        return boto_volume

    def attach_volume(self, ebs_volume, boto_volume):
        '''
        Attaches the given boto_volume class to the running instance
        '''
        if os.path.exists(ebs_volume.instance_device):
            logger.warn("The device {} already exists.".format(ebs_volume.instance_device))
        # attaching a volume to our instance

        message_format = 'Attaching volume %s to instance %s'
        logger.info(message_format, boto_volume.id, self.instance_id)
        self.con.attach_volume(
            boto_volume.id, self.instance_id, ebs_volume.device)

        logger.info('Starting to poll till volume is fully attached')
        # drink some coffee and wait
        waited = 0
        MAX_ATTACHMENT_WAIT = 45
        while boto_volume.update() != 'in-use' and waited < MAX_ATTACHMENT_WAIT:
            logger.info('Waiting for volume attachment: %s' % boto_volume.id)
            sleep(1)
            waited += 1
        while not os.path.exists(ebs_volume.instance_device) and waited < MAX_ATTACHMENT_WAIT:
            logger.info('Waiting for device: %s' % ebs_volume.instance_device)
            sleep(1)
            waited += 1

        if waited == MAX_ATTACHMENT_WAIT:
            error_format = 'Device didnt attach within % seconds'
            raise exceptions.AttachmentException(
                error_format, MAX_ATTACHMENT_WAIT)

        return boto_volume

    def detach_volume(self, ebs_volume, volume_id):
        detached = False
        MAX_DETACHMENT_WAIT = 45
        waited = 0
        logger.info('now detaching %s', volume_id)
        while os.path.exists(ebs_volume.instance_device) and waited < MAX_DETACHMENT_WAIT:
            logger.info('Waiting for device to detach: %s' %
                        ebs_volume.instance_device)
            detached = self.con.detach_volume(volume_id)
            sleep(1)
            waited += 1

        if waited == MAX_DETACHMENT_WAIT:
            error_format = 'Device didnt detach within % seconds'
            raise exceptions.DetachmentException(
                error_format, MAX_DETACHMENT_WAIT)

        return detached

    def get_bdm(self):
        bdm = self.con.get_instance_attribute(
            self.instance_id, 'blockDeviceMapping')
        return bdm

    def get_expiration_tags(self):
        tags = {
            'expires': str(datetime.now() + timedelta(days=self.SNAPSHOT_EXPIRY_DAYS)),
            'created': str(datetime.now()),
        }
        return tags

    def get_tags_for_volume(self, volume):
        '''
        Includes
        - filter tags (role, cluster, environment)
        - expiration tags (expires, created)
        - mount tag (mount point)
        - instance tag (for debugging)
        '''
        filter_tags = self.get_filter_tags()
        expiration_tags = self.get_expiration_tags()
        tags = dict(
            instance_id=self.instance_id,
            mount_point=volume.mount_point,
        )
        tags.update(filter_tags)
        tags.update(expiration_tags)
        return tags

    def get_volume_id(self, vol):
        bdm_mapping = self.bdm['blockDeviceMapping']
        try:
            volume_id = bdm_mapping[vol.device].volume_id
        except KeyError:
            msg = '%s not found in block device mapping %s' % (
                vol.device, bdm_mapping)
            raise exceptions.MissingVolume(msg)
        return volume_id

    def get_cached_snapshots(self):
        if not getattr(self, '_snapshots', None):
            tags = self.get_filter_tags()
            filters = {}
            for key, value in tags.iteritems():
                filters['tag:%s' % key] = value
            snapshots = self.con.get_all_snapshots(filters=filters)
            self._snapshots = snapshots
        return self._snapshots

    def get_snapshot(self, vol):
        """ Returns the ID of the most recent snapshot that matches the given tags, or None
            if no snapshots were found.

            tags is a dict, used to filter the results from get_all_snapshots.

            This relies on the fact that the API returns snapshots in the order they
            are created, so we can just return the last element of the list.
        """
        all_snapshots = self.get_cached_snapshots()
        all_snapshots.sort(key=lambda s: s.start_time, reverse=True)
        volume_snapshots = [s for s in all_snapshots if s.tags.get(
            'mount_point') == vol.mount_point]
        try:
            latest_snapshot = volume_snapshots[0]
        except IndexError, e:
            raise exceptions.MissingSnapshot(e.message)
        return latest_snapshot

    #Example, Redis.goteam.be snapshot of /mnt/persistent/
    SNAPSHOT_DESCRIPTION_FORMAT = "%(cluster)s snapshot of %(mount_point)s"

    def get_snapshot_description(self, vol):
        format_dict = dict(
            mount_point=vol.mount_point
        )
        format_dict.update(self.userdata)
        snapshot_name = self.SNAPSHOT_DESCRIPTION_FORMAT % format_dict
        snapshot_name = snapshot_name.replace('_', '-')
        return snapshot_name

    '''
    Shortcuts
    '''

    @property
    def instance_id(self):
        instance_id = self.metadata['instance-id']
        return instance_id

    @property
    def availability_zone(self):
        availability_zone = self.metadata['placement']['availability-zone']
        return availability_zone

    '''
    Section with Hooks
    '''

    def pre_mounts(self, volumes):
        pass

    def post_mounts(self, volumes):
        pass

    def pre_mount(self, vol):
        pass

    def post_mount(self, vol):
        pass

    def pre_unmounts(self, volumes):
        pass

    def post_unmounts(self, volumes):
        pass

    def pre_unmount(self, vol):
        pass

    def post_unmount(self, vol):
        pass

    def pre_snapshots(self, volumes):
        pass

    def post_snapshots(self, volumes):
        pass

    def pre_snapshot(self, vol):
        pass

    def post_snapshot(self, vol):
        pass
