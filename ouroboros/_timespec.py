#
# SPDX-FileCopyrightText: 2016 - 2026 Dimitri Staessens
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Shared float-seconds <-> ``struct timespec *`` conversions.

The caller passes its own ``ffi`` instance so the returned CData is
bound to the right CFFI extension module.
"""

from __future__ import annotations

from math import modf
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from cffi import FFI

BILLION = 1000 * 1000 * 1000


def fl_to_timespec(ffi: FFI, timeo: Optional[float]) -> Any:
    """
    Convert *timeo* (seconds, or None) to a ``struct timespec *``.

    *None* yields ``ffi.NULL`` (block forever). A non-positive *timeo*
    yields a zeroed timespec (async / poll).
    """

    if timeo is None:
        return ffi.NULL

    if timeo <= 0:
        return ffi.new("struct timespec *", [0, 0])

    frac, whole = modf(timeo)
    _timeo = ffi.new("struct timespec *")
    _timeo.tv_sec = int(whole)
    _timeo.tv_nsec = int(frac * BILLION)

    return _timeo


def timespec_to_fl(ffi: FFI, _timeo: Any) -> Optional[float]:
    """
    Convert a ``struct timespec *`` to seconds-as-float.

    ``ffi.NULL`` yields *None* (block forever).
    """

    if _timeo == ffi.NULL:
        return None

    if _timeo.tv_sec <= 0 and _timeo.tv_nsec == 0:
        return 0.0

    return _timeo.tv_sec + _timeo.tv_nsec / BILLION
