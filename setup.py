"""Build script for the PyOuroboros CFFI extensions.

Resolves the ouroboros library version via ``pkg-config`` and the
pyouroboros source version via ``setuptools_scm``, verifies that the
``major.minor`` halves match, and delegates the actual build to the
CFFI builders under ``ffi/``.
"""

from __future__ import annotations

import subprocess
import sys

from setuptools import setup
from setuptools_scm import get_version


def _get_ouroboros_version() -> str:
    try:
        out = subprocess.check_output(
            ['pkg-config', '--modversion', 'ouroboros-dev'],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("ERROR: ouroboros-dev not found via pkg-config. "
                 "Is Ouroboros installed?")


def _check_build_version_compat() -> None:
    try:
        pyo7s_ver = get_version(root='.', relative_to=__file__)
    except (LookupError, OSError):
        return  # no SCM info, skip check

    o7s_ver = _get_ouroboros_version()

    # setuptools_scm: '0.23.1.dev3+g<hash>' or '0.23.0'
    # pkg-config:     '0.23.0'
    # Compare major.minor only.
    o7s_parts   = o7s_ver.split('.')
    pyo7s_parts = pyo7s_ver.split('.')

    if o7s_parts[0] != pyo7s_parts[0] or o7s_parts[1] != pyo7s_parts[1]:
        sys.exit(
            f"ERROR: Version mismatch: ouroboros {o7s_ver} "
            f"vs pyouroboros {pyo7s_ver} "
            f"(major.minor must match)"
        )


_check_build_version_compat()

setup(
    cffi_modules=[
        "ffi/pyouroboros_build_dev.py:ffibuilder",
        "ffi/pyouroboros_build_irm.py:ffibuilder",
    ],
)
