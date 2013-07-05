from collections import defaultdict
from datetime import datetime, timedelta
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
        LOGGING_CONFIG = FILE_LOGGING_CONFIG
    except (ValueError, IOError, OSError), e:
        logger.warn('WARNING couldnt write log to files, got error %s', e)
    return LOGGING_CONFIG


def age_to_seconds(age):
    TIME_PERIODS = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 3600 * 24,
        'w': 3600 * 24 * 7
    }
    token = age[-1:].lower()
    if token not in TIME_PERIODS:
        raise TypeError('malformed time period, should be in %s' %
                        TIME_PERIODS.keys())
    return int(age[:-1]) * TIME_PERIODS[token]


def check_backups(max_age, environment, cluster, role):
    import dateutil.parser
    import pytz

    ec2 = get_ec2_conn()
    now = datetime.utcnow().replace(tzinfo=pytz.utc)

    tag_filters = {
        'tag:environment': environment,
        'tag:cluster': cluster,
        'tag:role': role,
        'status': 'in-use',
    }

    vols = ec2.get_all_volumes(filters=tag_filters)

    ids = []
    mountpoints = defaultdict(list)

    for vol in vols:
        ids.append(vol.id)
        mountpoints[vol.tags['mount_point']].append(vol.id)

    # filter snapshots with 1 day resolution
    limit = (datetime.now() - timedelta(days=(max_age - 1) // (24 * 3600)))

    snaps = ec2.get_all_snapshots(
        filters={
            'volume_id': ids,
            'start-time': "{}*".format(limit.date().isoformat())
        }
    )
    dones = {}
    for snap in snaps:
        mp = snap.tags['mount_point']
        start_time = dateutil.parser.parse(snap.start_time)

        # do a finer grain age check in python
        if (now - start_time) > timedelta(seconds=max_age):
            continue

        logger.info("Checking mountpoint {}".format(mp))

        # pop any accounted for mountpoints
        if snap.volume_id in mountpoints[mp]:
            dones[mp] = mountpoints.pop(mp)
        else:
            if mp in dones:
                mountpoints.pop(mp)

    if len(mountpoints.keys()) > 0:
        logger.warning("Some volumes are missing a recent snapshot \
            (cluster={}, env={}, role={}):".format(cluster, environment, role))

        for mp in mountpoints:
            logger.warning("\t* {} on volume(s) {}".format(
                mp, ", ".join(mountpoints[mp])))

    return len(mountpoints.keys())
