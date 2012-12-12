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
    def __init__(self, mount_point, freeze_command="fsfreeze"):
        self.mount_point = mount_point
        self.freeze_command = freeze_command

    def __enter__(self):
        from snaptastic.utils import is_root_dev
        # Freezing the root filesystem will cause the instance to become
        # permanently unresponsive, so let's make sure we don't do that
        root_dev = is_root_dev(self.mount_point)
        if root_dev:
            error_format = 'Refusing to freeze device, as its part of root "/" %s'
            raise FreezeException(error_format % self.mount_point)
        logger.info('Freezing %s', self.mount_point)
        subprocess.check_output(
            [self.freeze_command, '-f', self.mount_point], stderr=subprocess.STDOUT)

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info('Thawing %s', self.mount_point)
        subprocess.check_output([self.freeze_command, '-u', self.mount_point],
                                stderr=subprocess.STDOUT)


#normalizing name for context manager usage
freeze = Freeze
