#
# Ouroboros - Copyright (C) 2016 - 2026
#
# Internal helpers for translating float seconds <-> struct timespec.
#
#    Dimitri Staessens <dimitri@ouroboros.rocks>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# version 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., http://www.fsf.org/about/contact/.
#

"""Shared float-seconds <-> ``struct timespec *`` conversions.

The dev and event modules both deal in seconds-as-float timeouts on
the Python side and pass ``struct timespec *`` to the C library.
The helpers take the caller's ``ffi`` instance as a parameter so the
returned CData is bound to the right CFFI module.
"""

from __future__ import annotations

from math import modf
from typing import Optional

BILLION = 1000 * 1000 * 1000


def fl_to_timespec(ffi, timeo: Optional[float]):
    """Convert *timeo* (seconds, or None) to a ``struct timespec *``.

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


def timespec_to_fl(ffi, _timeo) -> Optional[float]:
    """Convert a ``struct timespec *`` to seconds-as-float.

    ``ffi.NULL`` yields *None* (block forever).
    """
    if _timeo == ffi.NULL:
        return None
    if _timeo.tv_sec <= 0 and _timeo.tv_nsec == 0:
        return 0.0
    return _timeo.tv_sec + _timeo.tv_nsec / BILLION
