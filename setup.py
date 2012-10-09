#!/usr/bin/env python
from setuptools import setup, find_packages
from snaptastic import __version__, __maintainer__, __email__


DESCRIPTION = """Snaptastic is a python tool to enable easy snapshotting
and mounting of snapshots on AWS/EC2 EBS volumes.
"""




tests_require = [
    'mock',
    'pep8',
    'coverage'
]

install_requires = []

license_text = open('LICENSE.txt').read()
long_description = open('README.md').read()
CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Scientific/Engineering :: Mathematics',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    name='snaptastic',
    version=__version__,
    author=__maintainer__,
    author_email=__email__,
    license=license_text,
    url='http://github.com/tschellenbach/Django-facebook',
    description=DESCRIPTION,
    long_description=long_description,
    packages=find_packages(exclude=("tests",)),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='snaptastic.tests',
    include_package_data=True,
    classifiers=CLASSIFIERS,
)
