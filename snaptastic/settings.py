from snaptastic.default_settings import *
import imp
import logging
import os

logger = logging.getLogger(__name__)

SETTING_FILE_LOCATIONS = [
    os.path.join('/etc', 'snaptastic_settings.py'),
    os.path.join('/etc', 'snaptastic', 'snaptastic_settings.py'),
]


SETTINGS_MODULE = None


def get_settings_module():
    '''
    This system searches for settings in the following locations:
       snaptastic_settings.py in sys.path
       and /etc/snaptastic_settings.py
       and /etc/snaptastic/snaptastic_settings.py
    '''
    settings_module = None
    try:
        import snaptastic_settings
        settings_module = snaptastic_settings
    except ImportError:
        for settings_file in SETTING_FILE_LOCATIONS:
            if os.path.isfile(settings_file):
                settings_module = imp.load_source(
                    'snaptastic_settings', settings_file)
                break
        else:
            error_format = 'Couldnt locate settings file in sys.path or %s'
            error_message = error_format % SETTING_FILE_LOCATIONS
            logger.warn(error_message)

    return settings_module


SETTINGS_MODULE = get_settings_module()

# import the settings
module_variables = [k for k in dir(
    SETTINGS_MODULE) if not k.startswith('_')]
module_dict = dict([(k, getattr(
    SETTINGS_MODULE, k)) for k in module_variables])
globals().update(module_dict)

# initializing the settings
from snaptastic.utils.log import dictConfig


def initialize_settings():
    '''
    Initialize the settings
    '''
    dictConfig(LOGGING_CONFIG)

initialize_settings()
