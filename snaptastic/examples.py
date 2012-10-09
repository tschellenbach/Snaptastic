from snaptastic import Snapshotter, EBSVolume, register


class TestSnapshotter(Snapshotter):
    name = 'test'

    def get_volumes(self):
        '''
        Get the volumes for this instance, customize this at will
        '''
        volume = EBSVolume(device='/dev/sdf', mount_point='/mnt/test', size=5)
        volumes = [volume]
        return volumes

register(TestSnapshotter)


class SOLRSnapshotter(Snapshotter):
    name = 'solr'

    def get_volumes(self):
        volume = EBSVolume('/dev/sdf1', '/mnt/index', size=200)
        volumes = [volume]
        return volumes

register(SOLRSnapshotter)


class PostgreSQLSnapshotter(Snapshotter):
    '''
    Customized mounting hooks for postgres
    '''
    name = 'postgres'

    def get_volumes(self):
        volume_dicts = [
            {"device": "/dev/sdf1", "mount_point":
                "/var/lib/postgresql/9.1/main", "size": 200},
            {"device": "/dev/sdf2", "mount_point":
                "/var/lib/postgresql/9.1/user_influence_history", "size": 2},
            {"device": "/dev/sdf3", "mount_point":
                "/var/lib/postgresql/9.1/entity_love", "size": 40},
            {"device": "/dev/sdf4", "mount_point":
                "/var/lib/postgresql/9.1/user_profile", "size": 10},
            {"device": "/dev/sdf5", "mount_point":
                "/var/lib/postgresql/9.1/entity_love_history", "size": 10},
            {"device": "/dev/sdf6", "mount_point":
                "/var/lib/postgresql/9.1/_user_profile_queue", "size": 8},
            {"device": "/dev/sdf7", "mount_point":
                "/var/lib/postgresql/9.1/entity_entity", "size": 40},
            {"device": "/dev/sdf8", "mount_point": "/var/lib/postgresql/9.1/event_framework_event_handler_queue", "size": 2},
            {"device": "/dev/sdf9", "mount_point": "/var/lib/postgresql/9.1/user_communication_queue", "size": 2},
            {"device": "/dev/sdi1", "mount_point": "/var/lib/postgresql/9.1/affiliate_click_tracking", "size": 50},
            {"device": "/dev/sdi2", "mount_point":
                "/var/lib/postgresql/9.1/index01", "size": 30},
            {"device": "/dev/sdi3", "mount_point":
                "/var/lib/postgresql/9.1/index02", "size": 30},
            {"device": "/dev/sdi4", "mount_point":
                "/var/lib/postgresql/9.1/index03", "size": 30},
            {"device": "/dev/sdi5", "mount_point":
                "/var/lib/postgresql/9.1/index04", "size": 30},
            {"device": "/dev/sdi6", "mount_point":
                "/var/lib/postgresql/9.1/index05", "size": 30}
        ]
        volumes = []
        for volume_dict in volume_dicts:
            volume = EBSVolume(**volume_dict)
            volumes.append(volume)
        return volumes

    def pre_mounts(self):
        import subprocess
        subprocess.check_output(['/etc/init.d/postgresql', 'stop'])

    def post_mounts(self):
        import subprocess
        # fix permissions on postgresql dirs
        subprocess.check_output(['chmod', '-R', '0700', '/var/lib/postgresql'])
        subprocess.check_output(
            ['chown', '-R', 'postgres:postgres', '/var/lib/postgresql'])


register(PostgreSQLSnapshotter)
