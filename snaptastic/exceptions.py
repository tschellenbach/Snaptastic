

class SnaptasticException(Exception):
    pass


class MissingSnapshot(SnaptasticException):
    pass


class FormattingException(SnaptasticException):
    pass


class SettingException(SnaptasticException):
    pass


class MissingVolume(SnaptasticException):
    pass


class RootFreeze(SnaptasticException):
    '''
    Dont try to freeze the root file system :)
    '''
    pass


class MountException(SnaptasticException):
    pass


class UnmountException(SnaptasticException):
    pass


class FormatException(SnaptasticException):
    pass


class AttachmentException(SnaptasticException):
    pass

class DetachmentException(SnaptasticException):
    pass


class DeviceAlreadyExists(SnaptasticException):
    pass
