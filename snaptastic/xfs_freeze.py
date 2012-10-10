import subprocess
import logging
import os

logger = logging.getLogger(__name__)


class FreezeException(Exception):
    pass


class Freeze(object):
    '''
    Context manager to freeze a given mount point
    '''
    def __init__(self, mount_point):
        self.mount_point = mount_point

    def __enter__(self):
        # Freezing the root filesystem will cause the instance to become
        # permanently unresponsive, so let's make sure we don't do that
        if os.stat('/')st_dev == os.stat(self.mount_point).st_dev:
            raise FreezeException(
                'Refusing to freeze device, as it contains "/"')
        logger.info('Freezing %s', self.mount_point)
        subprocess.check_output(
            ['xfs_freeze', '-f', self.mount_point], stderr=subprocess.STDOUT)

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info('Thawing %s', self.mount_point)
        subprocess.check_output(['xfs_freeze', '-u', self.mount_point],
                                stderr=subprocess.STDOUT)

#normalizing name for context manager usage
freeze = Freeze
