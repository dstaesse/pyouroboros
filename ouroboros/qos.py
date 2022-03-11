#
# Ouroboros - Copyright (C) 2016 - 2020
#
# Python API for applications - QoS
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

from _ouroboros_cffi import ffi
from math import modf
from typing import Optional

# Some constants
MILLION = 1000 * 1000
BILLION = 1000 * 1000 * 1000


class QoSSpec:
    """
    delay:        In ms, default 1000s
    bandwidth:    In bits / s, default 0
    availability: Class of 9s, default 0
    loss:         Packet loss in ppm, default MILLION
    ber:          Bit error rate, errors per billion bits. default BILLION
    in_order:     In-order delivery, enables FRCT, default 0
    max_gap:      Maximum interruption in ms, default MILLION
    cypher_s:     Requested encryption strength in bits
    timeout:      Peer timeout (ms), default 120000 (2 minutes)
    """

    def __init__(self,
                 delay: int = MILLION,
                 bandwidth: int = 0,
                 availability: int = 0,
                 loss: int = 1,
                 ber: int = MILLION,
                 in_order: int = 0,
                 max_gap: int = MILLION,
                 cypher_s: int = 0,
                 timeout: int = 120000):
        self.delay = delay
        self.bandwidth = bandwidth
        self.availability = availability
        self.loss = loss
        self.ber = ber
        self.in_order = in_order
        self.max_gap = max_gap
        self.cypher_s = cypher_s
        self.timeout = timeout


def _fl_to_timespec(timeo: float):
    if timeo is None:
        return ffi.NULL
    elif timeo <= 0:
        return ffi.new("struct timespec *", [0, 0])
    else:
        frac, whole = modf(timeo)
        _timeo = ffi.new("struct timespec *")
        _timeo.tv_sec = whole
        _timeo.tv_nsec = frac * BILLION
        return _timeo


def _timespec_to_fl(_timeo) -> Optional[float]:
    if _timeo is ffi.NULL:
        return None
    elif _timeo.tv_sec <= 0 and _timeo.tv_nsec == 0:
        return 0
    else:
        return _timeo.tv_sec + _timeo.tv_nsec / BILLION


def _qos_to_qosspec(qos: QoSSpec):
    if qos is None:
        return ffi.NULL
    else:
        return ffi.new("qosspec_t *",
                       [qos.delay,
                        qos.bandwidth,
                        qos.availability,
                        qos.loss,
                        qos.ber,
                        qos.in_order,
                        qos.max_gap,
                        qos.cypher_s,
                        qos.timeout])


def _qosspec_to_qos(_qos) -> Optional[QoSSpec]:
    if _qos is ffi.NULL:
        return None
    else:
        return QoSSpec(delay=_qos.delay,
                       bandwidth=_qos.bandwidth,
                       availability=_qos.availability,
                       loss=_qos.loss,
                       ber=_qos.ber,
                       in_order=_qos.in_order,
                       max_gap=_qos.max_gap,
                       cypher_s=_qos.cypher_s,
                       timeout=_qos.timeout)
