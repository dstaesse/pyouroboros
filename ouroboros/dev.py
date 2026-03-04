#
# Ouroboros - Copyright (C) 2016 - 2026
#
# Python API for Ouroboros
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

import errno
from enum import IntFlag
from math import modf
from typing import Optional

from _ouroboros_dev_cffi import ffi, lib
from ouroboros.qos import *

# Some constants
MILLION = 1000 * 1000
BILLION = 1000 * 1000 * 1000


def _fl_to_timespec(timeo: float):
    if timeo is None:
        return ffi.NULL
    elif timeo <= 0:
        return ffi.new("struct timespec *", [0, 0])
    else:
        frac, whole = modf(timeo)
        _timeo = ffi.new("struct timespec *")
        _timeo.tv_sec = int(whole)
        _timeo.tv_nsec = int(frac * BILLION)
        return _timeo


def _timespec_to_fl(_timeo) -> Optional[float]:
    if _timeo is ffi.NULL:
        return None
    elif _timeo.tv_sec <= 0 and _timeo.tv_nsec == 0:
        return 0
    else:
        return _timeo.tv_sec + _timeo.tv_nsec / BILLION


# Intentionally duplicated, dev uses a separate FFI (ouroboros-dev).
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
                       timeout=_qos.timeout)

# FRCT flags
FRCT_RETRANSMIT = 0o1
FRCT_RESCNTL    = 0o2
FRCT_LINGER     = 0o4


# ouroboros exceptions
class FlowAllocatedException(Exception):
    pass


class FlowNotAllocatedException(Exception):
    pass


class FlowDownException(Exception):
    pass


class FlowPermissionException(Exception):
    pass


class FlowException(Exception):
    pass


class FlowDeallocWarning(Warning):
    pass


def _raise(e: int) -> None:
    if e >= 0:
        return

    print("error: " + str(e))
    if e == -errno.ETIMEDOUT:
        raise TimeoutError()
    if e == -errno.EINVAL:
        raise ValueError()
    if e == -errno.ENOMEM:
        raise MemoryError()
    else:
        raise FlowException()


class FlowProperties(IntFlag):
    ReadOnly = 0o0
    WriteOnly = 0o1
    ReadWrite = 0o2
    Down = 0o4
    NonBlockingRead = 0o1000
    NonBlockingWrite = 0o2000
    NonBlocking = NonBlockingRead | NonBlockingWrite
    NoPartialRead = 0o10000
    NoPartialWrite = 0o200000


class Flow:

    def __init__(self):
        self.__fd: int = -1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        lib.flow_dealloc(self.__fd)

    def alloc(self,
              dst: str,
              qos: QoSSpec = None,
              timeo: float = None) -> Optional[QoSSpec]:
        """
        Allocates a flow with a certain QoS to a destination

        :param dst:   The destination name (string)
        :param qos:   The QoS for the requested flow (QoSSpec)
        :param timeo: The timeout for the flow allocation (None -> forever, 0->async)
        :return:      The QoS for the new flow
        """

        if self.__fd >= 0:
            raise FlowAllocatedException()

        _qos = _qos_to_qosspec(qos)

        _timeo = _fl_to_timespec(timeo)

        self.__fd = lib.flow_alloc(dst.encode(), _qos, _timeo)

        _raise(self.__fd)

        return _qosspec_to_qos(_qos)

    def accept(self,
               timeo: float = None) -> QoSSpec:
        """
        Accepts new flows and returns the QoS

        :param timeo: The timeout for the flow allocation (None -> forever, 0->async)
        :return:      The QoS for the new flow
        """

        if self.__fd >= 0:
            raise FlowAllocatedException()

        _qos = ffi.new("qosspec_t *")

        _timeo = _fl_to_timespec(timeo)

        self.__fd = lib.flow_accept(_qos, _timeo)

        _raise(self.__fd)

        return _qosspec_to_qos(_qos)

    def join(self,
             dst: str,
             timeo: float = None) -> None:
        """
        Join a broadcast layer

        :param dst:   The destination broadcast layer name (string)
        :param qos:   The QoS for the requested flow (QoSSpec)
        :param timeo: The timeout for the flow allocation (None -> forever, 0->async)
        :return:      The QoS for the flow
        """

        if self.__fd >= 0:
            raise FlowAllocatedException()

        _timeo = _fl_to_timespec(timeo)

        self.__fd = lib.flow_join(dst.encode(), _timeo)

        _raise(self.__fd)

    def dealloc(self):
        """
        Deallocate a flow

        """

        self.__fd = lib.flow_dealloc(self.__fd)

        if self.__fd < 0:
            raise FlowDeallocWarning

        self.__fd = -1

    def write(self,
              buf: bytes,
              count: int = None) -> int:
        """
        Attempt to write <count> bytes to a flow

        :param buf:    Buffer to write from
        :param count:  Number of bytes to write from the buffer
        :return:       Number of bytes written
        """

        if self.__fd < 0:
            raise FlowNotAllocatedException()

        if count is None:
            return lib.flow_write(self.__fd, ffi.from_buffer(buf), len(buf))

        return lib.flow_write(self.__fd, ffi.from_buffer(buf), count)

    def writeline(self,
                  ln: str) -> int:
        """
        Attempt to write a string to a flow

        :param ln:  String to write
        :return:    Number of bytes written
        """

        if self.__fd < 0:
            raise FlowNotAllocatedException()

        return self.write(ln.encode(), len(ln))

    def read(self,
             count: int = None) -> bytes:
        """
        Attempt to read bytes from a flow

        :param count:   Maximum number of bytes to read
        :return:        Bytes read
        """

        if self.__fd < 0:
            raise FlowNotAllocatedException()

        if count is None:
            count = 2048

        _buf = ffi.new("char []", count)

        result = lib.flow_read(self.__fd, _buf, count)

        return ffi.unpack(_buf, result)

    def readline(self):
        """

        :return: A string
        """
        if self.__fd < 0:
            raise FlowNotAllocatedException()

        return self.read().decode()

    # flow manipulation
    def set_snd_timeout(self,
                        timeo: float):
        """
        Set the timeout for blocking writes
        """
        _timeo = _fl_to_timespec(timeo)

        if lib.flow_set_snd_timeout(self.__fd, _timeo) != 0:
            raise FlowPermissionException()

    def get_snd_timeout(self) -> float:
        """
        Get the timeout for blocking writes

        :return: timeout for blocking writes
        """
        _timeo = ffi.new("struct timespec *")

        if lib.flow_get_snd_timeout(self.__fd, _timeo) != 0:
            raise FlowPermissionException()

        return _timespec_to_fl(_timeo)

    def set_rcv_timeout(self,
                        timeo: float):
        """
        Set the timeout for blocking writes
        """
        _timeo = _fl_to_timespec(timeo)

        if lib.flow_set_rcv_timeout(self.__fd, _timeo) != 0:
            raise FlowPermissionException()

    def get_rcv_timeout(self) -> float:
        """
        Get the timeout for blocking reads

        :return: timeout for blocking writes
        """
        _timeo = ffi.new("struct timespec *")

        if lib.flow_get_rcv_timeout(self.__fd, _timeo) != 0:
            raise FlowPermissionException()

        return _timespec_to_fl(_timeo)

    def get_qos(self) -> QoSSpec:
        """

        :return: Current QoS on the flow
        """
        _qos = ffi.new("qosspec_t *")

        if lib.flow_get_qos(self.__fd, _qos) != 0:
            raise FlowPermissionException()

        return _qosspec_to_qos(_qos)

    def get_rx_queue_len(self) -> int:
        """

        :return:
        """

        size = ffi.new("size_t *")

        if lib.flow_get_rx_qlen(self.__fd, size) != 0:
            raise FlowPermissionException()

        return int(size)

    def get_tx_queue_len(self) -> int:
        """

        :return:
        """

        size = ffi.new("size_t *")

        if lib.flow_get_tx_qlen(self.__fd, size) != 0:
            raise FlowPermissionException()

        return int(size)

    def set_flags(self, flags: FlowProperties):
        """
        Set flags for this flow.
        :param flags:
        """

        if lib.flow_set_flags(self.__fd, int(flags)):
            raise FlowPermissionException()

    def get_flags(self) -> FlowProperties:
        """
        Get the flags for this flow
        """

        flags = lib.flow_get_flags(self.__fd)
        if flags < 0:
            raise FlowPermissionException()

        return FlowProperties(int(flags))

    def set_frct_flags(self, flags: int):
        """
        Set FRCT flags for this flow.
        :param flags: Bitmask of FRCT_RETRANSMIT, FRCT_RESCNTL, FRCT_LINGER
        """

        if lib.flow_set_frct_flags(self.__fd, flags):
            raise FlowPermissionException()

    def get_frct_flags(self) -> int:
        """
        Get the FRCT flags for this flow

        :return: Bitmask of FRCT flags
        """

        flags = lib.flow_get_frct_flags(self.__fd)
        if flags < 0:
            raise FlowPermissionException()

        return int(flags)


def flow_alloc(dst: str,
               qos: QoSSpec = None,
               timeo: float = None) -> Flow:
    """

    :param dst:    Destination name
    :param qos:    Requested QoS
    :param timeo:  Timeout to wait for the allocation
    :return:       A new Flow()
    """

    f = Flow()
    f.alloc(dst, qos, timeo)
    return f


def flow_accept(timeo: float = None) -> Flow:
    """

    :param timeo:  Timeout to wait for the allocation
    :return:       A new Flow()
    """

    f = Flow()
    f.accept(timeo)
    return f


def flow_join(dst: str,
              qos: QoSSpec = None,
              timeo: float = None) -> Flow:
    """

    :param dst:    Broadcast layer name
    :param qos:    Requested QoS
    :param timeo:  Timeout to wait for the allocation
    :return:       A new Flow()
    """

    f = Flow()
    f.join(dst, qos, timeo)
    return f
