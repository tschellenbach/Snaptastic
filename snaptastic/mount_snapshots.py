#!/usr/bin/env python
""" mounts ebs volumes to this instance, using the latest version of the snapshot.
"""
from tagged_snapshots import get_volumes, get_snapshot, create_device, mount_device, configure_logging
from boto.utils import get_instance_userdata
import subprocess
from json import loads


def main():

    configure_logging('mount_snapshots.log')

    snap = Snapshotter()
    snap.mount_volumes()


if __name__ == '__main__':
    main()
