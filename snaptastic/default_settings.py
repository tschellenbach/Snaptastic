
import logging
from snaptastic.utils import setup_file_logging

logger = logging.getLogger(__name__)


BASE_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'basic': {
            'format': '%(message)s [%(name)s:%(levelname)s]'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout',
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'stream': 'ext://sys.stderr',
        },
    },
    'loggers': {
        'snaptastic': {
            'handlers': ['default', 'error'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}


# backport for dictconfig if we are running on 2.6
from snaptastic.utils import log
# backport check_output to support 2.6
from snaptastic.utils import sub

# setup the file logging if available
LOGGING_CONFIG = setup_file_logging(BASE_LOGGING_CONFIG)
