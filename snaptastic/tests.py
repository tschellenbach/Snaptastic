import sys
import os
import subprocess

path = os.path.abspath(__file__)
parent = os.path.join(path, '../', '../')
sys.path.append(parent)

import unittest2
import mock
from snaptastic import EBSVolume
from snaptastic.freeze import freeze
from snaptastic import Snapshotter
from snaptastic.ebs_volume import FILESYSTEMS as FS
from snaptastic import exceptions


class BaseTest(unittest2.TestCase):
    def setUp(self):
        pass

    def get_test_snapshotter(self):
        con = mock.Mock()
        userdata = dict(role='role', environment='test', cluster='cluster')
        placement = dict(instance_id='a123')
        placement['availability-zone'] = 'test-az'
        metadata = dict(placement=placement)
        metadata['instance-id'] = 'instance-id'
        mapping = dict()
        bdm = dict()
        mapping['/dev/sdf'] = mock.Mock()
        bdm['blockDeviceMapping'] = mapping
        snap = Snapshotter(userdata, metadata, con, bdm)
        snap.wait_before_attempt = mock.Mock()
        return snap


class TestFreeze(BaseTest):
    def test_freeze(self):
        with mock.patch('subprocess.check_output') as check:
            with mock.patch('snaptastic.utils.is_root_dev', return_value=False):
                for fs in [FS.EXT3, FS.EXT4, FS.REISERFS, FS.JFS, FS.XFS]:
                    vol = EBSVolume(
                        "/dev/sdf", "/mnt/test", size=1, file_system=fs,
                        check_support=False)
                    with vol.freeze():
                        check.assert_called_with(
                            [fs.freeze_cmd, '-f', '/mnt/test'],
                            stderr=subprocess.STDOUT)
                    check.assert_called_with(
                        [fs.freeze_cmd, '-u', '/mnt/test'], stderr=-2)

    def test_freeze_fail(self):
        with mock.patch('subprocess.check_output') as check:
            with mock.patch('snaptastic.utils.is_root_dev', return_value=False):
                for fs in [FS.EXT3, FS.EXT4, FS.REISERFS, FS.JFS, FS.XFS]:

                    vol = EBSVolume(
                        "/dev/sdf", "/mnt/test", size=1, file_system=fs,
                        check_support=False)
                    try:
                        with vol.freeze():
                            check.assert_called_with(
                                [fs.freeze_cmd, '-f', '/mnt/test'], stderr=subprocess.STDOUT)
                            raise Exception('test')
                    except:
                        pass
                    check.assert_called_with(
                        [fs.freeze_cmd, '-u', '/mnt/test'], stderr=subprocess.STDOUT)


class TestCreateSnapshot(BaseTest):
    def test_make_snapshots(self):
        snap = self.get_test_snapshotter()
        volume = EBSVolume(
            device='/dev/sdf', mount_point='/mnt/test', size=5,
            check_support=False)
        with mock.patch('subprocess.check_output') as check:
            with mock.patch('snaptastic.utils.is_root_dev', return_value=False):
                snap.make_snapshots([volume])
                self.assertEqual(check.call_count, 2)
                check.assert_called_with(
                    [volume.file_system.freeze_cmd, '-u', '/mnt/test'], stderr=subprocess.STDOUT)

    def test_make_snapshot(self):
        snap = self.get_test_snapshotter()
        con = snap.con
        volume = EBSVolume(
            device='/dev/sdf', mount_point='/mnt/test', size=5,
            check_support=False)
        with mock.patch('subprocess.check_output'):
            with mock.patch('snaptastic.utils.is_root_dev', return_value=False):
                snap.make_snapshot(volume)
        args, kwargs = con.create_snapshot.call_args
        description = kwargs['description']
        self.assertEqual(description, 'cluster snapshot of /mnt/test')

    def test_snapshot_name(self):
        snap = self.get_test_snapshotter()
        volume = EBSVolume(
            device='/dev/sdf', mount_point='/mnt/test', size=5,
            check_support=False)
        snapshot_name = snap.get_snapshot_description(volume)
        self.assertEqual(snapshot_name, 'cluster snapshot of /mnt/test')


class TestMounting(BaseTest):
    def test_mount_snapshots(self):
        snap = self.get_test_snapshotter()
        volume = EBSVolume(
            device='/dev/sdf', mount_point='/mnt/test', size=5,
            check_support=False)
        snap.get_snapshot = mock.Mock()
        snap.attach_volume = mock.Mock()
        snap.wait_for_snapshots = mock.Mock()
        with mock.patch('subprocess.check_output'):
            with mock.patch('os.makedirs'):
                snap.mount_snapshots([volume])

    def test_mount_iops_snapshots(self):
        snap = self.get_test_snapshotter()
        volume = EBSVolume(
            device='/dev/sdf', mount_point='/mnt/test', size=5, iops=1600,
            check_support=False)
        snap.get_snapshot = mock.Mock()
        snap.attach_volume = mock.Mock()
        snap.wait_for_snapshots = mock.Mock()
        with mock.patch('subprocess.check_output'):
            with mock.patch('os.makedirs'):
                snap.mount_snapshots([volume])

    def test_not_ready_snapshots_max_retries(self):
        snap = self.get_test_snapshotter()
        not_ready_snapshot = mock.Mock()
        snap.get_snapshot = mock.Mock(return_value=not_ready_snapshot)
        try:
            snap.wait_for_snapshots(['volume 1'], max_retries=3)
        except exceptions.MissingSnapshot:
            pass
        assert snap.wait_before_attempt.call_count == 3

    def test_not_ready_snapshots_exit(self):
        snap = self.get_test_snapshotter()
        not_ready_snapshot = mock.Mock()
        snap.get_snapshot = mock.Mock(return_value=not_ready_snapshot)
        with self.assertRaises(exceptions.MissingSnapshot):
            snap.wait_for_snapshots(['volume 1'])

    def test_ready_snapshots(self):
        snap = self.get_test_snapshotter()
        not_ready_snapshot = mock.Mock()
        not_ready_snapshot.status.return_value = 'completed'
        snap.get_snapshot = mock.Mock(return_value=not_ready_snapshot)
        snap.wait_for_snapshots(['volume 1'])

    def test_ready_snapshots_retry_ok(self):
        in_progress = ['completed', 'not ready', 'not ready']
        snap = self.get_test_snapshotter()
        not_ready_snapshot = mock.Mock()
        not_ready_snapshot.status.side_effect = lambda *x: in_progress.pop()
        snap.get_snapshot = mock.Mock(return_value=not_ready_snapshot)
        snap.wait_for_snapshots(['volume 1'])
        assert snap.wait_before_attempt.call_count == 2


class TestLogLevel(BaseTest):
    def test_loglevel(self):
        import logging
        # make sure settings are imported
        from snaptastic import settings
        from snaptastic.cli import configure_log_level
        for level in ['DEBUG', 'INFO', 'ERROR']:
            configure_log_level(level)
            level_object = getattr(logging, level)
            root_logger = logging.getLogger()
            set_level = root_logger.getEffectiveLevel()
            self.assertEqual(level_object, set_level)


if __name__ == '__main__':
    unittest2.main()
