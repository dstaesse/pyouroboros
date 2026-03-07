import subprocess
import sys

from setuptools import setup


def _get_ouroboros_version():
    try:
        out = subprocess.check_output(
            ['pkg-config', '--modversion', 'ouroboros-dev'],
            stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("ERROR: ouroboros-dev not found via pkg-config. "
                 "Is Ouroboros installed?")


def _check_build_version_compat():
    try:
        from setuptools_scm import get_version
        pyouro_ver = get_version(root='.', relative_to=__file__)
    except Exception:
        return  # no SCM info, skip check

    ouro_ver = _get_ouroboros_version()

    # setuptools_scm: '0.23.1.dev3+g<hash>' or '0.23.0'
    # pkg-config:     '0.23.0'
    # Compare major.minor only.
    ouro_parts   = ouro_ver.split('.')
    pyouro_parts = pyouro_ver.split('.')

    if ouro_parts[0] != pyouro_parts[0] or ouro_parts[1] != pyouro_parts[1]:
        sys.exit(
            f"ERROR: Version mismatch: ouroboros {ouro_ver} "
            f"vs pyouroboros {pyouro_ver} "
            f"(major.minor must match)"
        )


_check_build_version_compat()

setup(
    cffi_modules=[
        "ffi/pyouroboros_build_dev.py:ffibuilder",
        "ffi/pyouroboros_build_irm.py:ffibuilder"
    ],
)
