import sys

__author__ = 'Thierry Schellenbach'
__copyright__ = 'Copyright 2012, Thierry Schellenbach'
__credits__ = [
    'Mike Ryan, Thierry Schellenbach, mellowmorning.com, @tschellenbach']
__license__ = 'BSD'
__version__ = '0.2.2'
__maintainer__ = 'Thierry Schellenbach'
__email__ = 'thierryschellenbach@gmail.com'
__status__ = 'Production'

setup_install = 'setup.py' in sys.argv and 'install' in sys.argv

if not setup_install:
    from snaptastic.utils import get_ec2_conn, log, sub
    from snaptastic.metaclass import get_snapshotter
    from snapshotter import Snapshotter
    from ebs_volume import EBSVolume
    from snaptastic import settings

    #setup logging
    from snaptastic.utils.log import dictConfig
    dictConfig(settings.LOGGING_CONFIG)


if not setup_install:
    #register the examples
    from examples import *
