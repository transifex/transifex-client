#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
from codecs import BOM

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py

from txclib import get_version

readme_file = open(u'README.rst')
long_description = readme_file.read()
readme_file.close()
if long_description.startswith(BOM):
    long_description = long_description.lstrip(BOM)
long_description = long_description.decode('utf-8')

package_data = {
    '': ['LICENSE', 'README.rst'],
    'txclib': ['*.pem'],
}

scripts = ['tx']

install_requires = []
try:
    import json
except ImportError:
    install_requires.append('simplejson')

extra_args = {}
import platform
if platform.system() == 'Windows':
    import py2exe
    from py2exe.build_exe import py2exe as build_exe

    class MediaCollector(build_exe):
        # See http://crazedmonkey.com/blog/python/pkg_resources-with-py2exe.html
        def copy_extensions(self, extensions):
            build_exe.copy_extensions(self, extensions)
            self.copy_file(
                'txclib/cacert.pem',
                os.path.join(self.collect_dir, 'txclib/cacert.pem')
            )
            self.compiled_files.append('txclib/cacert.pem')

    extra_args = {
        'console': ['tx'],
        'options': {'py2exe': {'bundle_files': 1}},
        'zipfile': None,
        'cmdclass': {'py2exe': MediaCollector},
    }

setup(
    name="transifex-client",
    version=get_version(),
    scripts=scripts,
    description="A command line interface for Transifex",
    long_description=long_description,
    author="Transifex",
    author_email="admin@transifex.com",
    url="https://www.transifex.com",
    license="GPLv2",
    dependency_links=[
    ],
    setup_requires=[
    ],
    install_requires=install_requires,
    tests_require=["mock", ],
    data_files=[
    ],
    test_suite="tests",
    zip_safe=False,
    packages=['txclib', 'txclib.packages', 'txclib.packages.ssl_match_hostname'],
    include_package_data=True,
    package_data=package_data,
    keywords=('translation', 'localization', 'internationalization',),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    **extra_args
)
