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


def is_root_dev(mount_point):
    is_root_dev = os.stat('/').st_dev == os.stat(mount_point).st_dev
    return is_root_dev


def try_dict_config(dict_config):
    from snaptastic.utils.log import dictConfig
    try:
        dictConfig(dict_config)
    except ValueError, e:
        #if we have not file system
        dict_config['loggers']['snaptastic']['handlers'] = ['default']
        dictConfig(dict_config)
        logger.warn('Couldnt write logs to files, got error %s', e)
