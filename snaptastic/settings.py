from snaptastic import exceptions
from snaptastic.default_settings import *
import imp
import logging
import code
import traceback
import signal


logger = logging.getLogger(__name__)


setting_files = [
    os.path.join('/etc', 'snaptastic_settings.py'),
    os.path.join('/etc', 'snaptastic', 'snaptastic_settings.py'),
]
logger.info('trying snaptastic_settings in sys.path')
try:
    import snaptastic_settings
    from snaptastic_settings import *
    logger.info('found settings at %s', snaptastic_settings)
except ImportError, e:
    logger.info('didnt find snaptastic settings file in sys.path, search the filesystem')
    for settings_file in setting_files:
        logger.info('trying settings file %s', settings_file)
        if os.path.isfile(settings_file):

            snaptastic_settings = imp.load_source(
                'snaptastic_settings', settings_file)
            module_variables = [k for k in dir(
                snaptastic_settings) if not k.startswith('_')]
            module_dict = dict([(k, getattr(
                snaptastic_settings, k)) for k in module_variables])
            globals().update(module_dict)
            logger.info('found settings file at %s', settings_file)
            break
    else:
        raise exceptions.SettingException(
            'Couldnt locate settings file in sys.path or %s', setting_files)


def debug(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging."""
    # Allow access to frame object.
    d = {'_frame': frame}
    # Unless shadowed by global
    d.update(frame.f_globals)
    d.update(frame.f_locals)

    i = code.InteractiveConsole(d)
    message = "Signal recieved : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)

signal.signal(signal.SIGUSR1, debug)
