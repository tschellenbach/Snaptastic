############################################################################################################################################
Snaptastic by Mike Ryan & Thierry Schellenbach (`mellowmorning.com <http://www.mellowmorning.com/>`_)
############################################################################################################################################

About the Author
----------------

Mike Ryan, Syadmin at Fashiolista, author of ...
Thierry Schellenbach, Founder/ CTO at Fashiolista

.. image:: https://secure.travis-ci.org/tschellenbach/Snaptastic.png?branch=master

Example Settings File

REGION = 'eu-west-1'
AWS_ACCESS_KEY_ID = 'AKIAI3G42EFBKHLCPXFQ'
AWS_SECRET_ACCESS_KEY = 'AwRnLC0tGEYCXvWP71wc1RFXXI5QmoaiEeHs5VZJ'

#create snapshotters
from snaptastic import Snapshotter, EBSVolume

class SOLRSnapshotter(Snapshotter):
    def get_volumes(self):
        volume = EBSVolume('/dev/sdf1', '/mnt/index', size=200)
        volumes = [volume]
        return volumes

For more examples see examples.py

Snaptastic searches for its setting file at:
* snaptastic_settings on sys.path
* /etc/snaptastic_settings.py
* /etc/snaptastic/snaptastic_settings.py


Features

* Gracefull failure handling
* Freezes for the absoulte minimal required duration
* Batches boto API calls for faster batch volume mounting/snapshotting
* Tested codebase


Todo

* Prevent you from freezing the root filesystem
* Auto terminate volumes after instance termination
* Travis
* Pypi


Workflow

* fab validate (checks pep8 and unittests)
* fab publish (if tests are ok, publishes the new version, tag, pypi)
* fab clean (attempt to auto cleanup pep8 mistakes)

Django Jobs
-----------
Do you also see the beauty in clean code? Are you experienced with high scalability web apps?
Currently we're looking for additional talent over at our Amsterdam office.
Feel free to drop me a line at my personal email for more information: thierryschellenbach[at]gmail.com




