import subprocess
import logging

logger = logging.getLogger(__name__)


class Freeze(object):
    '''
    Context manager to freeze a given mount point
    '''
    def __init__(self, mount_point):
        self.mount_point = mount_point
    
    def __enter__(self):
        logger.info('Freezing %s', self.mount_point)
        #TODO: Validate that we're not freezing the root file system
        subprocess.check_output(['xfs_freeze', '-f', self.mount_point], stderr=subprocess.STDOUT)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info('Thawing %s', self.mount_point)
        subprocess.check_output(['xfs_freeze', '-u', self.mount_point],
            stderr=subprocess.STDOUT)

#normalizing name for context manager usage
freeze = Freeze