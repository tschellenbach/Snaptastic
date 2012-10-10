from snaptastic import exceptions
import logging
import os
import subprocess

logger = logging.getLogger(__name__)


class EBSVolume(object):
    '''
    Small wrapper class for specifying your desired EBS volume setup
    '''
    MOUNT_CMD = 'mount -t xfs -o defaults %(device)s %(mount_point)s'
    FORMAT_CMD = 'mkfs.xfs %(device)s'

    def __init__(self, device, size, mount_point=None):
        self.device = device
        self.size = size
        self.mount_point = mount_point

    def __repr__(self):
        return 'EBSVolume on %s from %s(%s)' % (self.mount_point, self.device, self.size)
            

    @property
    def instance_device(self):
        '''
        Ubuntu places the device under /dev/sdf in /dev/xvdf
        '''
        device = self.device.replace('sd', 'xvd')
        return device

    def mount(self):
        """ Mounts device as mount_point, creating mount_point and parent dirs if necessary.

            Note that the device sdf appears as xvdf, possibly because AWS uses pv-grub:
                https://forums.aws.amazon.com/thread.jspa?messageID=194798
        """
        if not os.path.exists(self.mount_point):
            os.makedirs(self.mount_point)
        try:
            logger.info('mounting device %s on %s',
                        self.instance_device, self.mount_point)
            cmd = self.MOUNT_CMD % {'device':
                                    self.instance_device, 'mount_point': self.mount_point}
            subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            msg = 'Error mounting %s: %s' % (self.instance_device, e.output)
            logger.error(msg)
            raise exceptions.MountException(msg)

    def format(self):
        '''
        Format the volume
        '''
        cmd = self.FORMAT_CMD % {'device': self.instance_device}
        try:
            logger.info('formatting device %s', self.instance_device)
            subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            msg = 'Error formatting %s: %s' % (self.instance_device, e.output)
            logger.error(msg)
            raise exceptions.FormattingException(msg)
