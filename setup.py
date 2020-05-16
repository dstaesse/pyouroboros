#!/usr/bin/env python

import setuptools

setuptools.setup(
    name='PyOuroboros',
    version=0.17,
    url='https://ouroboros.rocks',
    keywords='ouroboros IPC subsystem',
    author='Dimitri Staessens',
    author_email='dimitri@ouroboros.rocks',
    license='LGPLv2.1',
    description='Python API for Ouroboros',
    packages=[
        'ouroboros'
    ],
    setup_requires=[
        "cffi>=1.0.0"
    ],
    cffi_modules=[
        "ffi/pyouroboros_build.py:ffibuilder"
    ],
    install_requires=[
        "cffi>=1.0.0"
    ])
