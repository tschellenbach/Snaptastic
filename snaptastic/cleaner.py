import datetime
import collections
import logging
from snaptastic import get_ec2_conn, get_cloudwatch_conn
logger = logging.getLogger(__name__)


class Cleaner(object):
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
        # self.userdata = get_userdata_dict() if userdata is None else userdata
        # self.metadata = get_instance_metadata(
        # ) if metadata is None else metadata
        self.con = get_ec2_conn() if connection is None else connection

    def get_running_amis(self):
        reservations = self.con.get_all_instances()
        running_amis = collections.defaultdict(list)
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.state == 'running':
                    running_amis[instance.image_id].append(instance)
        return running_amis

    def get_running_instances(self):
        running_instances = []
        reservations = self.con.get_all_instances()
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.state == 'running':
                    running_instances.append(instance)
        return running_instances

    def cleanup_instances(self):
        instances = self.get_running_instances()
        running_instances = len(instances)
        logger.info('running %s instances', running_instances)
        c = get_cloudwatch_conn()

        low_utilized_instances = []

        class InstanceDimension(dict):
            def __init__(self, name, value):
                self[name] = value

        for instance in instances:
            from boto.exception import BotoServerError
            try:
                end = datetime.datetime.now()
                start = end - datetime.timedelta(days=1)
                stats = c.get_metric_statistics(
                    60 * 60 * 24,
                    start,
                    end,
                    'CPUUtilization',
                    'AWS/EC2',
                    'Average',
                    InstanceDimension("InstanceId", instance.id)
                )
                for stat in stats[-1:]:
                    average = stat['Average']
                    if average < 5:
                        instance.cpu_utilization = average
                        low_utilized_instances.append(instance)

            except BotoServerError, e:
                print e

        logger.info('found %s instances with low cpu utilization',
                    len(low_utilized_instances))
        from pprint import pprint
        for instance in low_utilized_instances:
            print '===' * 10
            print instance
            pprint(instance.get_attribute('userData'))
            pprint(instance.tags)

    def get_owners(self):
        owners = ['612857642705']
        return owners

    def get_our_amis(self):
        owners = self.get_owners()
        images = self.con.get_all_images(owners=owners)
        image_ids = []
        image_dict = collections.defaultdict(list)
        for image in images:
            image_dict[image.owner_id].append(image)
            image_ids.append(image.id)
        our_amis = set(image_ids)
        return our_amis

    def get_unused_amis(self):
        running_amis = set(self.get_running_amis())
        our_amis = set(self.get_our_amis())
        unused_amis = list(our_amis - running_amis)
        unused_amis.sort(key=lambda x: unicode(x))
        return unused_amis

    def get_missing_amis(self):
        running_amis_dict = self.get_running_amis()
        running_amis = set(running_amis_dict)
        our_amis = set(self.get_our_amis())
        missing_amis = list(running_amis - our_amis)
        missing_amis_dict = dict.fromkeys(missing_amis)
        for m in missing_amis:
            running = running_amis_dict[m]
            missing_amis_dict[m] = running
        return missing_amis_dict

    def delete_amis(self, unused_amis):
        for ami in unused_amis:
            logger.info('now removing %s', ami)
            self.con.deregister_image(ami)

    def get_our_snapshots(self):
        owners = self.get_owners()
        snapshots = self.con.get_all_snapshots(owner=owners[0])
        return snapshots

    def filter_expired_snapshots(self, snapshots):
        now = datetime.datetime.today()
        expired_snapshots = []
        for snapshot in snapshots:
            expiry_date = self.get_snapshot_expiry_date(snapshot)
            if expiry_date < now:
                expired_snapshots.append(snapshot)
        return expired_snapshots

    def delete_snapshots(self, snapshots):
        for snapshot in snapshots:
            print 'removing snapshot %s' % snapshot
            self.con.delete_snapshot(snapshot.id)

    def sum_snapshot_size(self, snapshots):
        volume_sizes = []
        for snapshot in snapshots:
            volume_sizes.append(snapshot.volume_size)
        total_volume = sum(volume_sizes)
        return total_volume

    EXPIRY_FORMAT_STRING = '%Y-%m-%d'

    def get_snapshot_expiry_date(self, snapshot):
        tags = snapshot.tags
        expiry_date_string = tags.get('expiry')
        expiry_delta = tags.get('expiry_delta')
        start_time = datetime.datetime.strptime(
            snapshot.start_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        if expiry_date_string:
            expiry_date = datetime.datetime.strptime(
                expiry_date_string, self.EXPIRY_FORMAT_STRING)
        elif expiry_delta:
            expiry_date = start_time + datetime.timedelta(days=expiry_delta)
        else:
            expiry_date = start_time + datetime.timedelta(days=3)
        return expiry_date

    def get_expired_snapshots(self):
        our_amis = self.get_our_amis()
        snapshots = self.get_our_snapshots()
        total_size = self.sum_snapshot_size(snapshots)
        print 'found %s snapshots in total, with size of %s GB' % (
            len(snapshots), total_size)
        print our_amis
        non_ami_snapshots = [s for s in snapshots if not any(
            [a in s.description for a in our_amis])]
        assert 'snap-7aa43b2c' not in non_ami_snapshots
        print 'found %s non ami snapshots' % len(non_ami_snapshots)
        expired_snapshots = self.filter_expired_snapshots(non_ami_snapshots)
        assert 'snap-7aa43b2c' not in expired_snapshots
        print 'found %s rotten snapshots from %s snapshots in total' % (
            len(expired_snapshots), len(non_ami_snapshots))
        return expired_snapshots

    def cleanup_snapshots(self):
        expired_snapshots = self.get_expired_snapshots()
        self.delete_snapshots(expired_snapshots)

    def useless_volumes(self):
        volumes = self.con.get_all_volumes()
        available_volumes = []
        for v in volumes:
            if v.status == 'available':
                available_volumes.append(v)
        return available_volumes

    def cleanup_volumes(self):
        useless_volumes = self.useless_volumes()
        self.delete_volumes(useless_volumes)

    def cleanup_images(self):
        unused_amis = self.get_unused_amis()
        for ami in unused_amis:
            print 'removing ami %s' % ami
            self.con.deregister_image(ami, delete_snapshot=True)

    def delete_volumes(self, volumes):
        for v in volumes:
            print 'removing volume v %s' % v.id
            v.delete()

    def clean(self, component):
        if component == 'volumes':
            self.cleanup_volumes()
        elif component == 'snapshots':
            self.cleanup_snapshots()
        elif component == 'images':
            self.cleanup_images()
        elif component == 'instances':
            self.cleanup_instances()
        elif component == 'all':
            self.cleanup_images()
            self.cleanup_volumes()
            self.cleanup_snapshots()
        else:
            raise ValueError('Dont know how to clean %s' % component)
