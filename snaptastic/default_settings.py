
import os
import sys
error_log_path = os.path.join('/var', 'log', 'snaptastic', 'error.log')
log_path = os.path.join('/var', 'log', 'snaptastic', 'info.log')

test_running = 'python -m unittest' in sys.argv


def ensure_dir(path):
    path_dir, filename = os.path.split(path)
    if not os.path.isdir(path_dir):
        os.makedirs(path_dir)



LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': error_log_path
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': log_path
        }

    },
    'loggers': {
        'snaptastic': {
            'handlers': ['default', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}


if test_running:
    LOGGING_CONFIG['loggers']['snaptastic']['handlers'] = ['default']
else:
    ensure_dir(error_log_path)
    ensure_dir(log_path)


#backport for dictconfig if we are running on 2.6
from snaptastic.utils import log
from snaptastic.utils.log import dictConfig
#backport check_output to support 2.6
from snaptastic.utils import sub
dictConfig(LOGGING_CONFIG)
