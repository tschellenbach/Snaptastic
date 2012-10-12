############################################################################################################################################
Snaptastic by Mike Ryan & Thierry Schellenbach [mellowmorning.com](http://www.mellowmorning.com/)
############################################################################################################################################

About the Author
----------------

Mike Ryan, Syadmin at Fashiolista, author of ...
Thierry Schellenbach, Founder/ CTO at Fashiolista

.. image:: https://secure.travis-ci.org/tschellenbach/Snaptastic.png?branch=master

Command line usage

start by validating if we can access boto and instance metadata
snaptastic test

roundtrip flow
snaptastic mount-snapshots solr
touch /mnt/test/helloworld.txt
snaptastic make-snapshots solr
snaptastic unmount-snapshots solr
df to verify its gone
snaptastic mount-snapshots solr




Example Settings File

    REGION = 'eu-west-1'
    AWS_ACCESS_KEY_ID = 'ExampleKey'
    AWS_SECRET_ACCESS_KEY = 'ExampleSecret'

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

* Graceful failure handling
* Freezes for the absolute minimal required duration
* Batches boto API calls for faster batch volume mounting/snapshotting
* Tested codebase

Porting old systems

You will often need to fake userdata for porting old systems.
Doing so is quite easy:

sudo snaptastic make-snapshots solr --userdata='{"role": "solr", "cluster": "solr", "environment": "aws"}'

Todo

* Prevent you from freezing the root filesystem
* Auto terminate volumes after instance termination
* Error testing against boto and real file system
* Pypi


Workflow

* fab validate (checks pep8 and unittests)
* fab publish (if tests are ok, publishes the new version, tag, pypi)
* fab clean (attempt to auto cleanup pep8 mistakes)

Running tests

* python -m unittest snaptastic.tests

Django Jobs
-----------
Do you also see the beauty in clean code? Are you experienced with high scalability web apps?
Currently we're looking for additional talent over at our Amsterdam office.
Feel free to drop me a line at my personal email for more information: thierryschellenbach[at]gmail.com




