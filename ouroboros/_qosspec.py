#
# SPDX-FileCopyrightText: 2016 - 2026 Dimitri Staessens
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Shared QoSSpec <-> qosspec_t conversion helpers.

CFFI types are not interchangeable across extension modules, so the
caller passes its own ``ffi`` instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ouroboros.qos import QoSSpec

if TYPE_CHECKING:
    from cffi import FFI


def qos_to_qosspec(ffi: FFI, qos: Optional[QoSSpec]) -> Any:
    """
    Convert a :class:`QoSSpec` to a freshly-allocated ``qosspec_t *``.

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


def qosspec_to_qos(ffi: FFI, _qos: Any) -> Optional[QoSSpec]:
    """
    Convert a ``qosspec_t *`` back to a :class:`QoSSpec`.

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
