
import os
import sys
error_log_path = os.path.join('/var', 'log', 'snaptastic', 'error.log')
log_path = os.path.join('/var', 'log', 'snaptastic', 'info.log')

test_running = 'python -m unittest' in sys.argv


def ensure_dir(path):
    path_dir, filename = os.path.split(path)
    if not os.path.isdir(path_dir):
        os.makedirs(path_dir)


ensure_dir(error_log_path)
ensure_dir(log_path)


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

import logging.config
logging.config.dictConfig(LOGGING_CONFIG)
