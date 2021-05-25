#!/usr/bin/env python3
# Copyright (c) 2021, Cisco Systems, Inc. and/or its affiliates
# Licensed under the MIT License, see the "LICENSE" file accompanying this file.

import re
import setuptools


def read_version():
    with open('orbital_api/version.py', 'r') as fin:
        return re.search(
            r"__version__ = '(?P<version>.+)'",
            fin.read().strip(),
        ).group('version')


def read_readme():
    with open('README.md', 'r') as fin:
        return fin.read().strip()


NAME = 'orbital_api'
VERSION = read_version()
DESCRIPTION = 'Cisco Orbital API Module'
LONG_DESCRIPTION = read_readme()
LONG_DESCRIPTION_CONTENT_TYPE = 'text/markdown'
URL = 'https://github.com/advthreat/orbital_api'
AUTHOR = 'Cisco Advanced Threat'
LICENSE = 'MIT'
PACKAGES = setuptools.find_packages(exclude=['tests', 'tests.*'])
PYTHON_REQUIRES = '>=3.0'
INSTALL_REQUIRES = [
    'requests',
    'urllib3'
]

KEYWORDS = [
    'cisco', 'security',
    'orbital', 'amp',
    'api', 'module',
    'python',
]

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setuptools.setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESCRIPTION_CONTENT_TYPE,
    url=URL,
    author=AUTHOR,
    license=LICENSE,
    packages=PACKAGES,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    keywords=KEYWORDS,
    classifiers=CLASSIFIERS,
    scripts=['orbital']
)
