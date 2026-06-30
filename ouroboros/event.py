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

"""Asynchronous flow event monitoring for Ouroboros."""

from __future__ import annotations

from enum import IntFlag
from typing import List, Optional, Tuple

from _ouroboros_dev_cffi import ffi, lib

from ouroboros._timespec import fl_to_timespec
from ouroboros.dev import Flow
from ouroboros.errors import FlowEventError, raise_errno


class FEventType(IntFlag):
    """Types of flow events."""
    FLOW_PKT     = lib.FLOW_PKT
    FLOW_DOWN    = lib.FLOW_DOWN
    FLOW_UP      = lib.FLOW_UP
    FLOW_ALLOC   = lib.FLOW_ALLOC
    FLOW_DEALLOC = lib.FLOW_DEALLOC
    FLOW_PEER    = lib.FLOW_PEER


class FEventQueue:
    """A queue of flow events waiting to be drained."""

    def __init__(self) -> None:
        self._fq = lib.fqueue_create()
        if self._fq == ffi.NULL:
            raise MemoryError("Failed to create FEventQueue")

    def __enter__(self) -> FEventQueue:
        return self

    def __exit__(self, exc_type, exc_value, tb) -> None:
        self.destroy()

    def __del__(self) -> None:
        self.destroy()

    def destroy(self) -> None:
        """Destroy the underlying queue. Idempotent."""
        if self._fq != ffi.NULL:
            lib.fqueue_destroy(self._fq)
            self._fq = ffi.NULL

    def next(self) -> Tuple[Flow, FEventType]:
        """Return the next ``(flow, event_type)`` pair from the queue."""
        fd = lib.fqueue_next(self._fq)
        raise_errno(fd, default=FlowEventError)

        _type = lib.fqueue_type(self._fq)
        raise_errno(_type, default=FlowEventError)

        return Flow(fd), FEventType(_type)

    @property
    def handle(self):
        """Return the underlying ``fqueue_t *``.

        Intended for use by :meth:`FlowSet.wait` within the same
        package; not part of the user-facing API.
        """
        return self._fq


class FlowSet:
    """A set of flows that can be monitored for events."""

    def __init__(self, flows: Optional[List[Flow]] = None) -> None:
        self._set = lib.fset_create()
        if self._set == ffi.NULL:
            raise MemoryError("Failed to create FlowSet")

        if flows is not None:
            for flow in flows:
                if lib.fset_add(self._set, flow.fileno()) != 0:
                    lib.fset_destroy(self._set)
                    self._set = ffi.NULL
                    raise MemoryError(f"Failed to add flow {flow.fileno()}.")

    def __enter__(self) -> FlowSet:
        return self

    def __exit__(self, exc_type, exc_value, tb) -> None:
        self.destroy()

    def __del__(self) -> None:
        self.destroy()

    def destroy(self) -> None:
        """Destroy the underlying set. Idempotent."""
        if self._set != ffi.NULL:
            lib.fset_destroy(self._set)
            self._set = ffi.NULL

    def add(self, flow: Flow) -> None:
        """Add *flow* to this set."""
        if self._set == ffi.NULL:
            raise ValueError("FlowSet has been destroyed")

        if lib.fset_add(self._set, flow.fileno()) != 0:
            raise MemoryError(f"Failed to add flow {flow.fileno()}")

    def zero(self) -> None:
        """Remove all flows from this set."""
        if self._set == ffi.NULL:
            raise ValueError("FlowSet has been destroyed")

        lib.fset_zero(self._set)

    def remove(self, flow: Flow) -> None:
        """Remove *flow* from this set."""
        if self._set == ffi.NULL:
            raise ValueError("FlowSet has been destroyed")

        lib.fset_del(self._set, flow.fileno())

    def wait(self,
             fq: FEventQueue,
             timeo: Optional[float] = None) -> None:
        """Wait for at least one event on one of the monitored flows.

        :param fq:    The :class:`FEventQueue` to drain events into.
        :param timeo: Wait timeout in seconds (None blocks forever).
        """
        if self._set == ffi.NULL:
            raise ValueError("FlowSet has been destroyed")

        _timeo = fl_to_timespec(ffi, timeo)

        rc = lib.fevent(self._set, fq.handle, _timeo)
        raise_errno(rc, default=FlowEventError)
