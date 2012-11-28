from snaptastic import exceptions
import logging
import os
import subprocess

logger = logging.getLogger(__name__)


class FILESYSTEMS:
    class XFS:
        pass

    class EXT4:
        pass


class EBSVolume(object):
    '''
    Small wrapper class for specifying your desired EBS volume setup
    '''
    MOUNT_CMD = 'mount -t xfs -o defaults %(device)s %(mount_point)s'
    UNMOUNT_CMD = 'umount %(device)s'
    FORMAT_CMD = 'mkfs.xfs %(device)s'

    def __init__(self, device, mount_point, size=5, delete_on_termination=True, file_system=FILESYSTEMS.XFS):
        self.device = device
        self.size = size
        self.mount_point = mount_point
        self.delete_on_termination = delete_on_termination
        self.file_system = file_system

    def __repr__(self):
        return 'EBSVolume on %s from %s(%s GB) is %s ' \
            % (self.mount_point, self.device, self.size, self.status)

    def status(self):
        if self.is_mounted():
            return "mounted"
        else:
            return "not mounted"

    def is_mounted(self):
        """ Assuming all mounts are done through snaptastic """
        return os.path.exists(self.mount_point)

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

    def unmount(self):
        try:
            mount_info = {'device': self.instance_device,
                          'mount_point': self.mount_point}
            cmd = self.UNMOUNT_CMD % mount_info
            logger.info('unmounting using command %s', cmd)
            subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            msg = 'Error unmounting %s: %s' % (self.instance_device, e.output)
            logger.error(msg)
            raise exceptions.UnmountException(msg)

    def format(self):
        '''
        Format the volume
        '''
        cmd = self.FORMAT_CMD % {'device': self.instance_device}
        try:
            logger.info('formatting device %s with command %s',
                        self.instance_device, cmd)
            subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            msg = 'Error formatting %s: %s' % (self.instance_device, e.output)
            logger.error(msg)
            raise exceptions.FormattingException(msg)
