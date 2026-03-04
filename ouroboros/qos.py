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

# Some constants
MILLION = 1000 * 1000
BILLION = 1000 * 1000 * 1000

DEFAULT_PEER_TIMEOUT = 120000
UINT32_MAX = 0xFFFFFFFF


class QoSSpec:
    """
    delay:        In ms, default UINT32_MAX
    bandwidth:    In bits / s, default 0
    availability: Class of 9s, default 0
    loss:         Packet loss, default 1
    ber:          Bit error rate, errors per billion bits, default 1
    in_order:     In-order delivery, enables FRCT, default 0
    max_gap:      Maximum interruption in ms, default UINT32_MAX
    timeout:      Peer timeout (ms), default 120000 (2 minutes)
    """

    def __init__(self,
                 delay: int = UINT32_MAX,
                 bandwidth: int = 0,
                 availability: int = 0,
                 loss: int = 1,
                 ber: int = 1,
                 in_order: int = 0,
                 max_gap: int = UINT32_MAX,
                 timeout: int = DEFAULT_PEER_TIMEOUT):
        self.delay = delay
        self.bandwidth = bandwidth
        self.availability = availability
        self.loss = loss
        self.ber = ber
        self.in_order = in_order
        self.max_gap = max_gap
        self.timeout = timeout
