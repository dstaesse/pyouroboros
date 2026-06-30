#
# Ouroboros - Copyright (C) 2016 - 2026
#
# Python API for Ouroboros - QoS
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

"""QoS specification for Ouroboros flows."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

DEFAULT_PEER_TIMEOUT = 120000
UINT32_MAX = 0xFFFFFFFF
UINT64_MAX = 0xFFFFFFFFFFFFFFFF


class QoSService(IntEnum):
    """Mirrors ``enum qos_service`` in ``ouroboros/qos.h``."""
    RAW     = 0  # No FRCT; best-effort raw messages
    MESSAGE = 1  # FRCT, reliable ordered messages
    STREAM  = 2  # FRCT, reliable ordered byte stream


@dataclass(frozen=True)
class QoSSpec:
    """QoS specification for a flow.

    Frozen so the module-level ``QOS_*`` predefined cubes are safe to
    share. Construct a new spec with ``dataclasses.replace(qos, ...)``
    or ``QoSSpec(...)`` to override fields.

    :ivar service:      :class:`QoSService` (gates FRCT when > 0).
    :ivar delay:        Maximum one-way delay in ms.
    :ivar bandwidth:    Required bandwidth in bits/s.
    :ivar availability: Class of 9s (number of nines of uptime).
    :ivar loss:         Maximum packet loss (per million).
    :ivar ber:          Maximum bit error rate (errors per billion).
    :ivar max_gap:      Maximum interruption in ms.
    :ivar timeout:      Peer timeout in ms (default 120000 ms).
    """
    service: QoSService = QoSService.RAW
    delay: int = UINT32_MAX
    bandwidth: int = 0
    availability: int = 0
    loss: int = 1
    ber: int = 1
    max_gap: int = UINT32_MAX
    timeout: int = DEFAULT_PEER_TIMEOUT


# Predefined QoS specs, mirroring the static const qosspec_t values in
# ouroboros/qos.h. "_safe" sets ber=0 (integrity check); "rt" trades
# reliability for latency.

QOS_RAW = QoSSpec(
    service=QoSService.RAW,
    delay=UINT32_MAX, bandwidth=0, availability=0,
    loss=1, ber=1,
    max_gap=UINT32_MAX, timeout=0)

QOS_RAW_SAFE = QoSSpec(
    service=QoSService.RAW,
    delay=UINT32_MAX, bandwidth=0, availability=0,
    loss=1, ber=0,
    max_gap=UINT32_MAX, timeout=0)

QOS_RT = QoSSpec(
    service=QoSService.MESSAGE,
    delay=100, bandwidth=UINT64_MAX, availability=3,
    loss=1, ber=1,
    max_gap=100, timeout=DEFAULT_PEER_TIMEOUT)

QOS_RT_SAFE = QoSSpec(
    service=QoSService.MESSAGE,
    delay=100, bandwidth=UINT64_MAX, availability=3,
    loss=1, ber=0,
    max_gap=100, timeout=DEFAULT_PEER_TIMEOUT)

QOS_MSG = QoSSpec(
    service=QoSService.MESSAGE,
    delay=1000, bandwidth=0, availability=0,
    loss=0, ber=0,
    max_gap=2000, timeout=DEFAULT_PEER_TIMEOUT)

QOS_STREAM = QoSSpec(
    service=QoSService.STREAM,
    delay=1000, bandwidth=0, availability=0,
    loss=0, ber=0,
    max_gap=2000, timeout=DEFAULT_PEER_TIMEOUT)
