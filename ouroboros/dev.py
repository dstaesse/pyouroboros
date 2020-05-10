#
# Ouroboros - Copyright (C) 2016 - 2020
#
# Python API for applications
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

from _ouroboros_cffi import ffi, lib
import errno
from enum import IntFlag
from ouroboros.qos import *
from ouroboros.qos import _qos_to_qosspec, _fl_to_timespec, _qosspec_to_qos, _timespec_to_fl

# Some constants
MILLION = 1000 * 1000
BILLION = 1000 * 1000 * 1000


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
             qos: QoSSpec = None,
             timeo: float = None) -> Optional[QoSSpec]:
        """
        Join a broadcast layer

        :param dst:   The destination broadcast layer name (string)
        :param qos:   The QoS for the requested flow (QoSSpec)
        :param timeo: The timeout for the flow allocation (None -> forever, 0->async)
        :return:      The QoS for the flow
        """

        if self.__fd >= 0:
            raise FlowAllocatedException()

        _qos = _qos_to_qosspec(qos)

        _timeo = _fl_to_timespec(timeo)

        self.__fd = lib.flow_join(dst.encode(), _qos, _timeo)

        _raise(self.__fd)

        return _qosspec_to_qos(_qos)

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
        else:
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

        if lib.flow_set_snd_timout(self.__fd, _timeo) != 0:
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

        if lib.flow_set_rcv_timout(self.__fd, _timeo) != 0:
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

        _flags = ffi.new("uint32_t *", int(flags))

        if lib.flow_set_flag(self.__fd, _flags):
            raise FlowPermissionException()

    def get_flags(self) -> FlowProperties:
        """
        Get the flags for this flow
        """

        flags = lib.flow_get_flag(self.__fd)
        if flags < 0:
            raise FlowPermissionException()

        return FlowProperties(int(flags))


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


