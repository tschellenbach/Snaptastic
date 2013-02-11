import logging
import os


logger = logging.getLogger(__name__)


def add_tags(object_, tags):
    for key, value in tags.iteritems():
        object_.add_tag(key, value)


def get_userdata_dict():
    from json import loads
    from boto.utils import get_instance_userdata
    userdata = loads(get_instance_userdata())
    return userdata


def get_ec2_conn():
    from snaptastic import settings
    from boto import ec2
    ec2_conn = ec2.connect_to_region(settings.REGION,
                                     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    return ec2_conn


def get_cloudwatch_conn():
    from snaptastic import settings
    from boto.ec2 import cloudwatch
    conn = cloudwatch.connect_to_region(settings.REGION,
                                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    return conn


def is_root_dev(mount_point):
    is_root_dev = os.stat('/').st_dev == os.stat(mount_point).st_dev
    return is_root_dev


def setup_file_logging(LOGGING_CONFIG):
    '''
    Try to log to
    /var/log/snaptastic/error.log
    /var/log/snaptastic/info.log

    If that doesn't work fallback to stream logging
    '''
    from copy import deepcopy
    LOGGING_CONFIG = deepcopy(LOGGING_CONFIG)
    from snaptastic.utils.log import dictConfig
    try:
        error_log_path = os.path.join('/var', 'log', 'snaptastic', 'error.log')
        log_path = os.path.join('/var', 'log', 'snaptastic', 'info.log')

        def ensure_dir(path):
            path_dir, filename = os.path.split(path)
            if not os.path.isdir(path_dir):
                os.makedirs(path_dir)

        ensure_dir(error_log_path)
        ensure_dir(log_path)

        FILE_HANDLERS = {
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': error_log_path,
                'formatter': 'detailed',
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': log_path,
                'formatter': 'detailed',
            }
        }
        FILE_LOGGING_CONFIG = deepcopy(LOGGING_CONFIG)
        FILE_LOGGING_CONFIG['handlers'].update(FILE_HANDLERS)
        FILE_LOGGING_CONFIG['loggers']['snaptastic']['handlers'] = [
            'default', 'file', 'error_file']
        dictConfig(FILE_LOGGING_CONFIG)
        LOGGING_CONFIG = FILE_LOGGING_CONFIG
    except (ValueError, IOError, OSError), e:
        logger.warn('WARNING couldnt write log to files, got error %s', e)
        dictConfig(LOGGING_CONFIG)
    return LOGGING_CONFIG
