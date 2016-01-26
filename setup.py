#!/usr/bin/env python
# -*- coding: utf-8 -*-
from codecs import open
from setuptools import setup

import txclib


def get_file_content(filename):
    with open(filename, 'r', encoding='UTF-8') as f:
        return f.read()

setup(
    name="transifex-client",
    version=txclib.__version__,
    entry_points={'console_scripts': ['tx=txclib.cmdline:main']},
    description="A command line interface for Transifex",
    long_description=get_file_content('README.rst'),
    author="Transifex",
    author_email="admin@transifex.com",
    url="https://www.transifex.com",
    license="GPLv2",
    dependency_links=[],
    setup_requires=[],
    install_requires=get_file_content('requirements.txt').splitlines(),
    tests_require=["mock"],
    data_files=[],
    test_suite="tests",
    zip_safe=False,
    packages=['txclib'],
    include_package_data=True,
    package_data={},
    keywords=('translation', 'localization', 'internationalization',),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.5',
    ],
)
