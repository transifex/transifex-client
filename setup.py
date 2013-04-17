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
    extra_args = {
        'console': ['tx'],
        'options': {'py2exe': {'bundle_files': 1}},
        'zipfile': None,
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
    dependency_links = [
    ],
    setup_requires = [
    ],
    install_requires = install_requires,
    tests_require = ["mock", ],
    data_files=[
    ],
    test_suite="tests",
    zip_safe=False,
    packages=['txclib', ],
    include_package_data=True,
    package_data = package_data,
    keywords = ('translation', 'localization', 'internationalization',),
    **extra_args
)
