from boto.utils import get_instance_metadata
from datetime import timedelta, datetime
from snaptastic import exceptions, get_ec2_conn
from snaptastic.ebs_volume import EBSVolume
from snaptastic.utils import get_userdata_dict, add_tags
from time import sleep
from xfs_freeze import freeze
import logging
import os

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
        snapshot_name = self.get_snapshot_name(vol)
        logger.info('creating a snapshot with name %s', snapshot_name)
        # find the volume ID for this device
        volume_id = self.get_volume_id(vol)
        #get the tags, note that these are used for finding the right snapshot
        tags = self.get_expiration_tags()
        tags['mount_point'] = vol.mount_point
        #Don't freeze more than we need to
        with freeze(vol.mount_point):
            snapshot = self.con.create_snapshot(
                volume_id, description=snapshot_name)
        #Add tags
        add_tags(snapshot, tags)
        return snapshot

    def mount_volumes(self, volumes=None):
        '''
        Loops through the volumes and runs mount_volume on them
        '''
        volumes = volumes or self.get_volumes()
        logger.info('preparing to mount %s volumes', len(volumes))
        self.pre_mounts(volumes)
        for vol in volumes:
            self.pre_mount(vol)
            self.mount_volume(vol)
            self.post_mount(vol)

        self.post_mounts(volumes)

        return volumes

    def mount_volume(self, ebs_volume):
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
        snapshot_id = self.get_snapshot(ebs_volume)
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
        boto_volume = self.con.create_volume(size=vol.size,
                                             zone=self.availability_zone,
                                             snapshot=snapshot_id
                                             )
        # tag the volume
        tags = self.get_expiration_tags()
        tags['mount-point'] = vol.mount_point
        add_tags(boto_volume, tags)

        return boto_volume

    def attach_volume(self, ebs_volume, boto_volume):
        '''
        Attaches the given boto_volume class to the running instance
        '''
        # attaching a volume to our instance
        logging.info('Attaching volume %s to instance %s' % (
            boto_volume.id, self.instance_id))
        self.con.attach_volume(
            boto_volume.id, self.instance_id, ebs_volume.device)

        # drink some coffee and wait
        while boto_volume.update() != 'in-use':
            logging.info('Waiting for volume attachment: %s' % boto_volume.id)
            sleep(1)
        while not os.path.exists(ebs_volume.instance_device):
            logging.info('Waiting for device: %s' % ebs_volume.instance_device)
            sleep(1)
            
        return boto_volume
    
    def get_bdm(self):
        bdm = self.con.get_instance_attribute(
            self.instance_id, 'blockDeviceMapping')
        return bdm

    def get_context_tags(self):
        tags = {
            'role': self.userdata['role'],
            'cluster': self.userdata['cluster'],
            'environment': self.userdata['environment']
        }
        return tags

    def get_expiration_tags(self):
        context_tags = self.get_context_tags()
        tags = {
            'expires': str(datetime.now() + timedelta(days=self.SNAPSHOT_EXPIRY_DAYS)),
            'created': str(datetime.now()),
        }
        context_tags.update(tags)
        return context_tags

    def get_volume_id(self, vol):
        bdm_mapping = self.bdm['blockDeviceMapping']
        instance_device = vol.instance_device
        try:
            volume_id = bdm_mapping[instance_device].volume_id
        except KeyError:
            msg = '%s not found in block device mapping' % instance_device
            raise exceptions.MissingVolume(msg)
        return volume_id

    def get_cached_snapshots(self):
        if not getattr(self, '_snapshots', None):
            tags = self.get_context_tags()
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
        all_snapshots.sort(key=lambda s: s.created, reverse=True)
        volume_snapshots = [s for s in all_snapshots if s.tags.get(
            'mount_point') == vol.mount_point]
        try:
            snapshot = volume_snapshots[-1]
        except IndexError, e:
            raise exceptions.MissingSnapshot(e.message)
        return snapshot

    SNAPSHOT_NAME_FORMAT = "snapshot-%(role)s-%(environment)s-%(cluster)s-%(mount_point)s"

    def get_snapshot_name(self, vol):
        format_dict = dict(
            mount_point=vol.mount_point
        )
        format_dict.update(self.userdata)
        snapshot_name = self.SNAPSHOT_NAME_FORMAT % format_dict
        snapshot_name = snapshot_name.replace('_', '-')
        return snapshot_name

    '''
    Shortcuts
    '''

    @property
    def instance_id(self):
        instance_id = self.metadata['placement']['instance_id']
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

    def pre_snapshots(self, volumes):
        pass

    def post_snapshots(self, volumes):
        pass

    def pre_snapshot(self, vol):
        pass

    def post_snapshot(self, vol):
        pass
