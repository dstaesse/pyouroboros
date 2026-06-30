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

"""Flow allocation, acceptance and I/O for the Ouroboros dev API."""

from __future__ import annotations

import warnings
from enum import IntFlag
from typing import Optional

from _ouroboros_dev_cffi import ffi, lib

from ouroboros._qosspec import qos_to_qosspec, qosspec_to_qos
from ouroboros._timespec import fl_to_timespec, timespec_to_fl
from ouroboros.errors import (
    FlowAlreadyAllocatedError,
    FlowDeallocWarning,
    FlowNotAllocatedError,
    check_ouroboros_version,
    raise_errno,
)
from ouroboros.qos import QoSSpec

check_ouroboros_version(lib.OUROBOROS_VERSION_MAJOR,
                        lib.OUROBOROS_VERSION_MINOR)


class FrctFlags(IntFlag):
    """FRCT-level feature flags."""
    RETRANSMIT = 0o1
    RESCNTL    = 0o2
    LINGER     = 0o4


class FlowProperties(IntFlag):
    """Flags describing flow properties and blocking behaviour."""
    READ_ONLY          = 0o0
    WRITE_ONLY         = 0o1
    READ_WRITE         = 0o2
    DOWN               = 0o4
    NON_BLOCKING_READ  = 0o1000
    NON_BLOCKING_WRITE = 0o2000
    NON_BLOCKING       = NON_BLOCKING_READ | NON_BLOCKING_WRITE
    NO_PARTIAL_READ    = 0o10000
    NO_PARTIAL_WRITE   = 0o20000


class Flow:
    """Represents an allocated Ouroboros flow."""

    def __init__(self, fd: int = -1) -> None:
        """Construct a Flow wrapper.

        :param fd: Existing flow descriptor to wrap, or -1 for an
                   unallocated Flow that will be populated by
                   :meth:`alloc`, :meth:`accept` or :meth:`join`.
        """
        self._fd: int = fd

    def __enter__(self) -> Flow:
        return self

    def __exit__(self, exc_type, exc_value, tb) -> None:
        self.dealloc()

    def __del__(self) -> None:
        try:
            self.dealloc()
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # interpreter shutdown may have torn down lib already

    def __repr__(self) -> str:
        return f"Flow(fd={self._fd})"

    def fileno(self) -> int:
        """Return the underlying ouroboros flow descriptor."""
        return self._fd

    def alloc(self,
              dst: str,
              qos: Optional[QoSSpec] = None,
              timeo: Optional[float] = None) -> Optional[QoSSpec]:
        """Allocate a flow with a certain QoS to a destination.

        :param dst:   Destination name.
        :param qos:   Requested QoS.
        :param timeo: Allocation timeout (None blocks forever, 0 is async).
        :return:      The QoS the IRM granted for the new flow.
        """
        if self._fd >= 0:
            raise FlowAlreadyAllocatedError()

        _qos = qos_to_qosspec(ffi, qos)
        _timeo = fl_to_timespec(ffi, timeo)

        rc = lib.flow_alloc(dst.encode(), _qos, _timeo)
        raise_errno(rc)
        self._fd = rc

        return qosspec_to_qos(ffi, _qos)

    def accept(self,
               timeo: Optional[float] = None) -> Optional[QoSSpec]:
        """Accept an incoming flow and return its QoS.

        :param timeo: Accept timeout (None blocks forever, 0 is async).
        :return:      The QoS of the accepted flow.
        """
        if self._fd >= 0:
            raise FlowAlreadyAllocatedError()

        _qos = ffi.new("qosspec_t *")
        _timeo = fl_to_timespec(ffi, timeo)

        rc = lib.flow_accept(_qos, _timeo)
        raise_errno(rc)
        self._fd = rc

        return qosspec_to_qos(ffi, _qos)

    def join(self,
             dst: str,
             timeo: Optional[float] = None) -> None:
        """Join a broadcast layer.

        :param dst:   Destination broadcast layer name.
        :param timeo: Join timeout (None blocks forever, 0 is async).
        """
        if self._fd >= 0:
            raise FlowAlreadyAllocatedError()

        _timeo = fl_to_timespec(ffi, timeo)

        rc = lib.flow_join(dst.encode(), _timeo)
        raise_errno(rc)
        self._fd = rc

    def dealloc(self) -> None:
        """Deallocate this flow. Idempotent: a no-op on an unallocated flow."""
        if self._fd < 0:
            return
        rc = lib.flow_dealloc(self._fd)
        self._fd = -1
        if rc < 0:
            warnings.warn(f"flow_dealloc returned {rc}",
                          FlowDeallocWarning, stacklevel=2)

    def write(self,
              buf: bytes,
              count: Optional[int] = None) -> int:
        """Write up to *count* bytes to the flow.

        :param buf:   Buffer to write from.
        :param count: Number of bytes to write (defaults to ``len(buf)``).
        :return:      Number of bytes written.
        :raises FlowError: (or subclass) on negative ouroboros return codes.
        """
        if self._fd < 0:
            raise FlowNotAllocatedError()

        if count is None:
            count = len(buf)

        rc = lib.flow_write(self._fd, ffi.from_buffer(buf), count)
        return raise_errno(rc)

    def writeline(self,
                  ln: str) -> int:
        """Encode *ln* as UTF-8 and write it to the flow.

        :param ln: String to write.
        :return:   Number of bytes written.
        """
        if self._fd < 0:
            raise FlowNotAllocatedError()

        data = ln.encode()
        return self.write(data, len(data))

    def read(self,
             count: Optional[int] = None) -> bytes:
        """Read up to *count* bytes from the flow.

        :param count: Maximum number of bytes to read (default 2048).
        :return:      Bytes read (may be empty when an SDU was just
                      fully consumed by a previous matching read).
        :raises FlowError: (or subclass) on negative ouroboros return codes.
        """
        if self._fd < 0:
            raise FlowNotAllocatedError()

        if count is None:
            count = 2048

        _buf = ffi.new("char []", count)

        rc = lib.flow_read(self._fd, _buf, count)
        raise_errno(rc)

        return ffi.unpack(_buf, rc)

    def readline(self) -> str:
        """Read from the flow and decode the result as UTF-8."""
        if self._fd < 0:
            raise FlowNotAllocatedError()

        return self.read().decode()

    def set_snd_timeout(self, timeo: float) -> None:
        """Set the timeout for blocking writes (seconds)."""
        _timeo = fl_to_timespec(ffi, timeo)
        raise_errno(lib.flow_set_snd_timeout(self._fd, _timeo))

    def get_snd_timeout(self) -> Optional[float]:
        """Return the timeout for blocking writes (seconds)."""
        _timeo = ffi.new("struct timespec *")
        raise_errno(lib.flow_get_snd_timeout(self._fd, _timeo))
        return timespec_to_fl(ffi, _timeo)

    def set_rcv_timeout(self, timeo: float) -> None:
        """Set the timeout for blocking reads (seconds)."""
        _timeo = fl_to_timespec(ffi, timeo)
        raise_errno(lib.flow_set_rcv_timeout(self._fd, _timeo))

    def get_rcv_timeout(self) -> Optional[float]:
        """Return the timeout for blocking reads (seconds)."""
        _timeo = ffi.new("struct timespec *")
        raise_errno(lib.flow_get_rcv_timeout(self._fd, _timeo))
        return timespec_to_fl(ffi, _timeo)

    def get_qos(self) -> Optional[QoSSpec]:
        """Return the current QoS in effect on the flow."""
        _qos = ffi.new("qosspec_t *")
        raise_errno(lib.flow_get_qos(self._fd, _qos))
        return qosspec_to_qos(ffi, _qos)

    def get_rx_queue_len(self) -> int:
        """Return the receive queue length (bytes)."""
        size = ffi.new("size_t *")
        raise_errno(lib.flow_get_rx_qlen(self._fd, size))
        return int(size[0])

    def get_tx_queue_len(self) -> int:
        """Return the transmit queue length (bytes)."""
        size = ffi.new("size_t *")
        raise_errno(lib.flow_get_tx_qlen(self._fd, size))
        return int(size[0])

    def get_mtu(self) -> int:
        """Return the per-packet MTU.

        This is the maximum user payload that fits in one n-1 PDU,
        after crypto headers. Returns 0 if unknown.
        """
        mtu = ffi.new("size_t *")
        raise_errno(lib.flow_get_mtu(self._fd, mtu))
        return int(mtu[0])

    def set_flags(self, flags: FlowProperties) -> None:
        """Replace the full set of flags for this flow.

        .. warning::
            This OVERWRITES the entire ``oflags`` value, including
            the access-mode bits (``READ_ONLY`` / ``WRITE_ONLY`` /
            ``READ_WRITE``). Passing only ``NO_PARTIAL_READ`` (for
            example) silently downgrades the flow to read-only and
            subsequent writes will fail with :class:`FlowPermissionError`.

            To preserve the existing access mode use
            :meth:`add_flags` / :meth:`remove_flags`, or read the
            current flags with :meth:`get_flags` and OR in the new
            bits explicitly.

        :param flags: Bitmask of :class:`FlowProperties` values.
        """
        raise_errno(lib.flow_set_flags(self._fd, int(flags)))

    def add_flags(self, flags: FlowProperties) -> None:
        """OR *flags* into the current ``oflags`` value.

        Preserves the access mode and any other already-set bits.
        """
        current = self.get_flags()
        self.set_flags(current | FlowProperties(int(flags)))

    def remove_flags(self, flags: FlowProperties) -> None:
        """Clear *flags* from the current ``oflags`` value.

        Preserves every other bit (including the access mode).
        """
        current = self.get_flags()
        self.set_flags(current & ~FlowProperties(int(flags)))

    def get_flags(self) -> FlowProperties:
        """Return the current flags for this flow."""
        flags = raise_errno(lib.flow_get_flags(self._fd))
        return FlowProperties(int(flags))

    def set_frct_flags(self, flags: FrctFlags) -> None:
        """Set FRCT flags for this flow.

        :param flags: Bitmask of :class:`FrctFlags`.
        """
        raise_errno(lib.flow_set_frct_flags(self._fd, int(flags)))

    def get_frct_flags(self) -> FrctFlags:
        """Return the FRCT flags for this flow."""
        flags = raise_errno(lib.flow_get_frct_flags(self._fd))
        return FrctFlags(int(flags))

    def set_frct_max_sdu(self, size: int) -> None:
        """Set the maximum reassembly SDU size for FRCT (bytes)."""
        raise_errno(lib.flow_set_frct_max_sdu(self._fd, size))

    def get_frct_max_sdu(self) -> int:
        """Return the maximum reassembly SDU size for FRCT (bytes)."""
        size = ffi.new("size_t *")
        raise_errno(lib.flow_get_frct_max_sdu(self._fd, size))
        return int(size[0])

    def set_frct_rcv_ring_size(self, size: int) -> None:
        """Set the stream receive ring size (bytes, power of two)."""
        raise_errno(lib.flow_set_frct_rcv_ring_sz(self._fd, size))

    def get_frct_rcv_ring_size(self) -> int:
        """Return the stream receive ring size (bytes)."""
        size = ffi.new("size_t *")
        raise_errno(lib.flow_get_frct_rcv_ring_sz(self._fd, size))
        return int(size[0])

    def set_frct_rto_min(self, rto_ns: int) -> None:
        """Set the FRCT RTO floor (nanoseconds)."""
        raise_errno(lib.flow_set_frct_rto_min(self._fd, rto_ns))

    def get_frct_rto_min(self) -> int:
        """Return the FRCT RTO floor (nanoseconds)."""
        rto = ffi.new("time_t *")
        raise_errno(lib.flow_get_frct_rto_min(self._fd, rto))
        return int(rto[0])


def flow_alloc(dst: str,
               qos: Optional[QoSSpec] = None,
               timeo: Optional[float] = None) -> Flow:
    """Allocate a new flow and return the :class:`Flow` wrapper.

    :param dst:   Destination name.
    :param qos:   Requested QoS.
    :param timeo: Allocation timeout (None blocks forever, 0 is async).
    """
    f = Flow()
    f.alloc(dst, qos, timeo)
    return f


def flow_accept(timeo: Optional[float] = None) -> Flow:
    """Accept an incoming flow and return the :class:`Flow` wrapper.

    :param timeo: Accept timeout (None blocks forever, 0 is async).
    """
    f = Flow()
    f.accept(timeo)
    return f


def flow_join(dst: str,
              timeo: Optional[float] = None) -> Flow:
    """Join a broadcast layer and return the :class:`Flow` wrapper.

    :param dst:   Broadcast layer name.
    :param timeo: Join timeout (None blocks forever, 0 is async).
    """
    f = Flow()
    f.join(dst, timeo)
    return f
