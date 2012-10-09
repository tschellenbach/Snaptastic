'''

Snapshotter class
- instantiate with context, metadata and connection
- pre snapshots hook
- pre snapshot hook
- post snapshot hook
- post snapshots hook
- get_snapshot_for_mount_point function


Volume class
- device
- instance device
- size
- mount_point
- mount function
- attach function
- get_latest_snapshot function

Freeze context manager
- good tutorial
http://www.doughellmann.com/PyMOTW/contextlib/

'''

# wark around to allow setup.py to import from snaptastic.meta instead of here
from snaptastic.meta import __author__, __copyright__, __credits__, __license__
from snaptastic.meta import __version__, __maintainer__, __email__, __status__


from snaptastic.utils import get_ec2_conn
from snapshotter import Snapshotter
from ebs_volume import EBSVolume
from snaptastic import settings


import logging.config
logging.config.dictConfig(settings.LOGGING_CONFIG)

snapshotters = {}


def register(snapshotter):
    '''
    Register your snapshotter
    '''
    snapshotters[snapshotter.name] = snapshotter


def get_snapshotter(snapshotter_name):
    error_format = 'No Snapshotter %s defined, registered Snapshotters are %s'
    if not snapshotter_name in snapshotters:
        raise ValueError(
            error_format % (snapshotter_name, snapshotters.keys()))
    return snapshotters[snapshotter_name]


#register the examples
from examples import *
