#
# Ouroboros - Copyright (C) 2016 - 2026
#
# Internal helpers for translating QoSSpec <-> CFFI qosspec_t.
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

"""Shared QoSSpec <-> qosspec_t conversion helpers.

dev.py and irm.py each link against their own CFFI extension module
(``_ouroboros_dev_cffi`` and ``_ouroboros_irm_cffi``), so they each
have their own ``ffi`` instance and their own ``qosspec_t`` type.
CFFI types are not interchangeable across modules, so these helpers
take the caller's ``ffi`` instance as a parameter.
"""

from __future__ import annotations

from typing import Optional

from ouroboros.qos import QoSSpec


def qos_to_qosspec(ffi, qos: Optional[QoSSpec]):
    """Convert a :class:`QoSSpec` to a freshly-allocated ``qosspec_t *``.

    Returns ``ffi.NULL`` when *qos* is ``None``.
    """
    if qos is None:
        return ffi.NULL
    return ffi.new("qosspec_t *",
                   [qos.service,
                    qos.delay,
                    qos.bandwidth,
                    qos.availability,
                    qos.loss,
                    qos.ber,
                    qos.max_gap,
                    qos.timeout])


def qosspec_to_qos(ffi, _qos) -> Optional[QoSSpec]:
    """Convert a ``qosspec_t *`` back to a :class:`QoSSpec`.

    Returns ``None`` when *_qos* is ``ffi.NULL``.
    """
    if _qos == ffi.NULL:
        return None
    return QoSSpec(service=_qos.service,
                   delay=_qos.delay,
                   bandwidth=_qos.bandwidth,
                   availability=_qos.availability,
                   loss=_qos.loss,
                   ber=_qos.ber,
                   max_gap=_qos.max_gap,
                   timeout=_qos.timeout)
