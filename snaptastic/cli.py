import sys
import os
import logging
logger = logging.getLogger('snaptastic.cli')

path = os.path.abspath(__file__)
parent = os.path.join(path, '../', '../')
sys.path.append(parent)

from argh import command, ArghParser
from snaptastic import get_snapshotter
import json


def configure_snapshotter(snapshotter_name, userdata=None):
    snapshotter_class = get_snapshotter(snapshotter_name)
    if userdata:
        userdata = json.loads(userdata)
    snap = snapshotter_class(userdata=userdata)
    return snap


@command
def make_snapshots(snapshotter_name, userdata=None, verbosity=2):
    snap = configure_snapshotter(snapshotter_name, userdata)
    snap.make_snapshots()


@command
def mount_snapshots(snapshotter_name, userdata=None, verbosity=2,
                    ignore_mounted=False):
    snap = configure_snapshotter(snapshotter_name, userdata)
    snap.mount_snapshots(ignore_mounted=ignore_mounted)


@command
def unmount_snapshots(snapshotter_name, userdata=None, verbosity=2):
    unmount = raw_input("Are you sure you want to unmount?: ")
    if unmount in ['y', 'yeay', 'yes']:
        snap = configure_snapshotter(snapshotter_name, userdata)
        snap.unmount_snapshots()


@command
def list_volumes(snapshotter_name, userdata=None, verbosity=2):
    snap = configure_snapshotter(snapshotter_name, userdata)
    volumes = snap.get_volumes()
    for volume in volumes:
        print volume


@command
def clean(component, userdata=None, verbosity=2):
    from snaptastic.cleaner import Cleaner
    clean = raw_input("Are you sure you want to clean?(y,yeay,yes): ")
    if clean in ['y', 'yeay', 'yes']:
        cleaner = Cleaner()
        cleaner.clean(component)


@command
def test(verbosity=2):
    from snaptastic.utils import get_userdata_dict
    logger.info('trying to get userdata, requires boto and valid keys')
    try:
        userdata = get_userdata_dict()
        logger.info('found userdata, so that works %s', userdata)
    except Exception, e:
        logger.exception('Userdata lookup doesnt work, error %s', e)
    logger.info('next up instance metadata')
    from boto.utils import get_instance_metadata
    try:
        metadata = get_instance_metadata()
        logger.info('found instance metadata %s', metadata)
    except Exception, e:
        logger.exception('Metadata lookup doesnt work, error %s', e)


def main():
    pass

from snaptastic import __version__
if '--version' in sys.argv:
    print 'Snaptastic version %s' % __version__


p = ArghParser()
commands = [make_snapshots, mount_snapshots,
            list_volumes, unmount_snapshots, clean, test]
p.add_commands(commands)
p.dispatch()
