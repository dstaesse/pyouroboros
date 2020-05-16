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

from ouroboros.dev import *
from ouroboros.qos import _fl_to_timespec


# async API
class FlowEventError(Exception):
    pass


class FEventType(IntFlag):
    FlowPkt = lib.FLOW_PKT
    FlowDown = lib.FLOW_DOWN
    FlowUp = lib.FLOW_UP
    FlowAlloc = lib.FLOW_ALLOC
    FlowDealloc = lib.FLOW_DEALLOC


class FEventQueue:
    """
    A queue of events waiting to be handled
    """

    def __init__(self):
        self.__fq = lib.fqueue_create()
        if self.__fq is ffi.NULL:
            raise MemoryError("Failed to create FEventQueue")

    def __del__(self):
        lib.fqueue_destroy(self.__fq)

    def next(self):
        """
        Get the next event
        :return: Flow and eventtype on that flow
        """
        f = Flow()
        f._Flow__fd = lib.fqueue_next(self.__fq)
        if f._Flow__fd < 0:
            raise FlowEventError

        _type = lib.fqueue_type(self.__fq)
        if _type < 0:
            raise FlowEventError

        return f, _type


class FlowSet:
    """
    A set of flows that can be monitored for events
    """
    def __init__(self,
                 flows: [Flow] = None):

        self.__set = lib.fset_create()
        if self.__set is ffi.NULL:
            raise MemoryError("Failed to create FlowSet")

        if flows is not None:
            for flow in flows:
                if lib.fset_add(self.__set, flow._Flow__fd) != 0:
                    lib.fset_destroy(self.__set)
                    self.__set = ffi.NULL
                    raise MemoryError("Failed to add flow " + str(flow._Flow__fd) + ".")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        lib.fset_destroy(self.__set)

    def add(self,
            flow: Flow):
        """
        Add a Flow

        :param flow: The flow object to add
        """

        if self.__set is ffi.NULL:
            raise ValueError

        if lib.fset_add(self.__set, flow._Flow___fd) != 0:
            raise MemoryError("Failed to add flow")

    def zero(self):
        """
        Remove all Flows from this set
        """

        if self.__set is ffi.NULL:
            raise ValueError

        lib.fset_zero(self.__set)

    def remove(self,
               flow: Flow):
        """
        Remove a flow from a set

        :param flow:
        """

        if self.__set is ffi.NULL:
            raise ValueError

        lib.fset_del(self.__set, flow._Flow__fd)

    def wait(self,
             fq: FEventType,
             timeo: float = None):
        """
        Wait for at least one event on one of the monitored flows
        """

        if self.__set is ffi.NULL:
            raise ValueError

        _timeo = _fl_to_timespec(timeo)

        ret = lib.fevent(self.__set, fq._FEventQueue__fq, _timeo)
        if ret < 0:
            raise FlowEventError

    def destroy(self):
        lib.fset_destroy(self.__set)
