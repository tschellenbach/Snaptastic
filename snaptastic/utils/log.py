import logging
import sys


# Make sure a NullHandler is available
# This was added in Python 2.7/3.2
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

# Make sure that dictConfig is available
# This was added in Python 2.7/3.2
try:
    from logging.config import dictConfig
except ImportError:
    from snaptastic.utils.dictconfig import dictConfig


if sys.version_info < (2, 5):
    class LoggerCompat(object):
        def __init__(self, logger):
            self._logger = logger

        def __getattr__(self, name):
            val = getattr(self._logger, name)
            if callable(val):
                def _wrapper(*args, **kwargs):
                    # Python 2.4 logging module doesn't support 'extra' parameter to
                    # methods of Logger
                    kwargs.pop('extra', None)
                    return val(*args, **kwargs)
                return _wrapper
            else:
                return val

    def getLogger(name=None):
        return LoggerCompat(logging.getLogger(name=name))
else:
    getLogger = logging.getLogger

# Ensure the creation of the Django logger
# with a null handler. This ensures we don't get any
# 'No handlers could be found for logger "django"' messages
logger = getLogger('django')
if not logger.handlers:
    logger.addHandler(NullHandler())
