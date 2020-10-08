#!/usr/bin/env python
# -*- coding: utf-8 -*-
from codecs import open
from setuptools import setup

import txclib


def get_file_content(filename):
    with open(filename, "r", encoding="UTF-8") as f:
        return f.read()


setup(
    name="transifex-client",
    version=txclib.__version__,
    entry_points={"console_scripts": ["tx=txclib.cmdline:main"]},
    description="A command line interface for Transifex",
    long_description=get_file_content("README.md"),
    long_description_content_type="text/markdown",
    author="Transifex",
    author_email="admin@transifex.com",
    url="https://www.transifex.com",
    license="GPLv2",
    dependency_links=[],
    setup_requires=[],
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,<3.10",
    install_requires=get_file_content("requirements.txt").splitlines(),
    tests_require=["mock>=3.0.5,<4.0"],
    data_files=[],
    test_suite="tests",
    zip_safe=False,
    packages=["txclib"],
    include_package_data=True,
    package_data={},
    keywords=("translation", "localization", "internationalization",),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
