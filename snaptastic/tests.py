
import sys
import os
import subprocess

path = os.path.abspath(__file__)
parent = os.path.join(path, '../', '../')
sys.path.append(parent)

import unittest2
import mock
from snaptastic import EBSVolume
from snaptastic.xfs_freeze import freeze
from snaptastic import Snapshotter


class BaseTest(unittest2.TestCase):
    def setUp(self):
        pass

    def get_test_snapshotter(self):
        con = mock.Mock()
        userdata = dict(role='role', environment='test', cluster='cluster')
        placement = dict(instance_id='a123')
        placement['availability-zone'] = 'test-az'
        metadata = dict(placement=placement)
        mapping = dict()
        bdm = dict()
        mapping['/dev/sdf'] = mock.Mock()
        bdm['blockDeviceMapping'] = mapping
        snap = Snapshotter(userdata, metadata, con, bdm)
        return snap


class TestFreeze(unittest2.TestCase):
    def test_freeze(self):
        with mock.patch('subprocess.check_output') as check:
            with mock.patch('snaptastic.utils.is_root_dev', return_value=False):
                with freeze('/mnt/test/'):
                    check.assert_called_with(
                        ['xfs_freeze', '-f', '/mnt/test/'],
                        stderr=subprocess.STDOUT)
                check.assert_called_with(
                    ['xfs_freeze', '-u', '/mnt/test/'], stderr=-2)

    def test_freeze_fail(self):
        with mock.patch('subprocess.check_output') as check:
            with mock.patch('snaptastic.utils.is_root_dev', return_value=False):
                try:
                    with freeze('/mnt/test/'):
                        check.assert_called_with(['xfs_freeze', '-f', '/mnt/test/'], stderr=subprocess.STDOUT)
                        raise Exception('test')
                except:
                    pass
                check.assert_called_with(
                    ['xfs_freeze', '-u', '/mnt/test/'], stderr=subprocess.STDOUT)


class TestCreateSnapshot(BaseTest):
    def test_make_snapshots(self):
        snap = self.get_test_snapshotter()
        volume = EBSVolume(device='/dev/sdf', mount_point='/mnt/test', size=5)
        with mock.patch('subprocess.check_output') as check:
            with mock.patch('snaptastic.utils.is_root_dev', return_value=False):
                snap.make_snapshots([volume])
                self.assertEqual(check.call_count, 2)
                check.assert_called_with(
                    ['xfs_freeze', '-u', '/mnt/test'], stderr=subprocess.STDOUT)

    def test_make_snapshot(self):
        snap = self.get_test_snapshotter()
        con = snap.con
        volume = EBSVolume(device='/dev/sdf', mount_point='/mnt/test', size=5)
        with mock.patch('subprocess.check_output'):
            with mock.patch('snaptastic.utils.is_root_dev', return_value=False):
                snap.make_snapshot(volume)
        args, kwargs = con.create_snapshot.call_args
        description = kwargs['description']
        self.assertEqual(description, 'snapshot-role-test-cluster-/mnt/test')

    def test_snapshot_name(self):
        snap = self.get_test_snapshotter()
        volume = EBSVolume(device='/dev/sdf', mount_point='/mnt/test', size=5)
        snapshot_name = snap.get_snapshot_name(volume)
        self.assertEqual(snapshot_name, 'snapshot-role-test-cluster-/mnt/test')


class TestMounting(BaseTest):
    def test_mount_snapshots(self):
        snap = self.get_test_snapshotter()
        volume = EBSVolume(device='/dev/sdf', mount_point='/mnt/test', size=5)
        snap.get_snapshot = mock.Mock(return_value='1234')
        snap.attach_volume = mock.Mock()
        with mock.patch('subprocess.check_output'):
            with mock.patch('os.makedirs'):
                mounted = snap.mount_snapshots([volume])


if __name__ == '__main__':
    unittest2.main()
