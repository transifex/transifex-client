#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
from setuptools import setup

from txclib import get_version

readme_file = io.open('README.rst', 'rt', encoding='UTF-8')
long_description = readme_file.read()
readme_file.close()

package_data = {
    '': ['LICENSE', 'README.rst'],
}

scripts = ['tx']

install_requires = []
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
    packages=[
        'txclib', 'txclib.packages', 'txclib.packages.urllib3',
        'txclib.packages.urllib3.contrib',
        'txclib.packages.urllib3.packages',
        'txclib.packages.urllib3.packages.ssl_match_hostname',
    ],
    include_package_data=True,
    package_data=package_data,
    keywords=('translation', 'localization', 'internationalization',),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],
    **extra_args
)
