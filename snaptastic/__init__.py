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


__author__ = 'Thierry Schellenbach'
__copyright__ = 'Copyright 2012, Thierry Schellenbach'
__credits__ = [
    'Mike Ryan, Thierry Schellenbach, mellowmorning.com, @tschellenbach']
__license__ = 'BSD'
__version__ = '0.0.1'
__maintainer__ = 'Thierry Schellenbach'
__email__ = 'thierryschellenbach@gmail.com'
__status__ = 'Production'


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
