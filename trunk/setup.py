"""
$Id: setup.py 1875 2008-08-23 05:26:15Z fairwinds.dp $

Copyright (c) 2007 - 2010 ifPeople, Kapil Thangavelu, and Contributors
All rights reserved. Refer to LICENSE.txt for details of distribution and use.

Distutils setup

"""

import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '0.4.0'

setup(
    name='getpaid.authorizedotnet',
    version=version,
    license = 'ZPL2.1',
    description='GetPaid authorize.net payment processor functionality',
    long_description = (
        read('README.txt')
        + '\n' +
        read('CHANGES.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('src', 'getpaid', 'authorizedotnet', 'README.txt')
        + '\n' +
        'Download\n'
        '**********************\n'
        ),
    classifiers=[
        'Framework :: Plone',
        'Framework :: Zope3',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Operating System :: OS Independent',
        'Topic :: Office/Business :: Financial',
        'Topic :: Software Development :: Libraries',
        ],
    keywords='',
    author='getpaid community',
    author_email='getpaid-dev@googlegroups.com',
    url='http://code.google.com/p/getpaid',
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['getpaid'],
    include_package_data=True,
    install_requires = [ 'getpaid.core',
                         'setuptools',
                         'zc.authorizedotnet',
                         'zope.interface',
                         'zope.component',
                         'zope.annotation',
                         'M2Crypto'
                         ],
    zip_safe = False,
    )
