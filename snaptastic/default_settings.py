
import os
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
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join('/var', 'log', 'snaptastic', 'error.log')
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join('/var', 'log', 'snaptastic', 'info.log')
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

import logging.config
logging.config.dictConfig(LOGGING_CONFIG)
