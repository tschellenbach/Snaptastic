Snaptastic by Mike Ryan & Thierry Schellenbach ([mellowmorning.com](http://www.mellowmorning.com/))
-------------------------------------------------------------------------------------------------

Snaptastic allows you to automate the snapshotting (backup) and mounting of volumes
on your EC2 instances.

It uses tagging of snapshots to figure out which snapshot should be used to populate a volume upon boot.

About the Author
----------------

 - Thierry Schellenbach, Founder & CTO at Fashiolista
 - Mike Ryan, Syadmin at Fashiolista

![Travis CI](https://secure.travis-ci.org/tschellenbach/Snaptastic.png?branch=master "Travis CI")

Install
-------

**pip**

```python
pip install snaptastic
```

**settings file**

Create a settings file
**/etc/snaptastic/snaptastic_settings.py**
```python
AWS_ACCESS_KEY_ID = 'key'
AWS_SECRET_ACCESS_KEY = 'secret'
REGION = 'eu-west-1'

from snaptastic import Snapshotter, EBSVolume


class SolrSnapshotter(Snapshotter):
    name = 'solr'
    
    def get_volumes(self):
        volume = EBSVolume('/dev/sdf', '/mnt/solr', size=20)
        volumes = [volume]
        return volumes
```

**verifying**

```python
sudo snaptastic test
sudo snaptastic list-volumes solr
```

That's it, you're now ready to use snaptastic.

Tutorial
--------

**mount**

```python
snaptastic mount-snapshots solr
```
you should now have a mounted volume on /mnt/solr/

```bash
lets add a file to it
sudo touch /mnt/solr/helloworld
```

**make snapshots**

time to make a snapshot of this important change
```python
snaptastic make-snapshots solr
```

**destroying our work**
```python
snaptastic unmount-snapshots solr
```
check to see if /mnt/solr/ is actually gone

**restoring from backups**
```python
snaptastic mount-snapshots solr
```

customizing the tagging
-----------------------

When mounting volumes, snaptastic will search for snapshots with the correct tags.
By default it will look for:

 * role
 * cluster
 * environment
 * mount point (you're advised not to change this)

To uniquely identify snapshots to application logic.
Changing the tags which are used to fit with your application setup is trivial.
Simply subclass the snapshotter class and change the get_filter_tags function.
Have a look at the example below:

```python
class CustomFilterSnapshotter(Snapshotter):
    name = 'filter_example'
    
    def get_filter_tags(self):
        '''
        The tags which are used for finding the correct snapshot to load from.
        In addition to these tags, mount point is also always added.
        
        Use these to unique identify different parts of your infrastructure
        '''
        tags = {
            'group': self.userdata['group'],
        }
        return tags
```


settings file
-------------

For more examples see examples.py

Snaptastic searches for its setting file at:
* snaptastic_settings on sys.path
* /etc/snaptastic_settings.py
* /etc/snaptastic/snaptastic_settings.py


Features
--------

* Graceful failure handling
* Freezes for the absolute minimal required duration
* Batches boto API calls for faster batch volume mounting/snapshotting
* Tested codebase

Porting old systems
-------------------

You will often need to fake userdata for porting old systems.
Doing so is quite easy:

sudo snaptastic make-snapshots solr --userdata='{"role": "solr", "cluster": "solr", "environment": "aws"}'

Todo
----

* Auto terminate volumes after instance termination
* Auto detect region for cross region usage
* Ext4 support

Contributing & Project Workflow
-------------------------------

Contributions are more than welcome. Have a look at the Todo to get an idea of what's still missing. Please always add unittests (where possible) for your feature/bug.

 * fab validate (checks pep8 and unittests)
 * fab publish (if tests are ok, publishes the new version, tag, pypi)
 * fab clean (attempt to auto cleanup pep8 mistakes)

Running tests
-------------

* python -m unittest snaptastic.tests


Django Jobs
-----------
Do you also see the beauty in clean code? Are you experienced with high scalability web apps?
Currently we're looking for additional talent over at our Amsterdam office.
Feel free to drop me a line at my personal email for more information: thierryschellenbach[at]gmail.com



