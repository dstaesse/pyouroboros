#
# SPDX-FileCopyrightText: 2016 - 2026 Dimitri Staessens
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Exception hierarchy and errno translation for pyouroboros.

The ``E*`` constants mirror the Ouroboros-specific errno values in
``include/ouroboros/errno.h``.
"""

from __future__ import annotations

import errno
import os
from importlib.metadata import PackageNotFoundError, version

ENOTALLOC  = 1000  # Flow is not allocated
EIPCPTYPE  = 1001  # Unknown IPCP type
EIRMD      = 1002  # Failed to communicate with IRMD
EIPCP      = 1003  # Failed to communicate with IPCP
EIPCPSTATE = 1004  # Target in wrong state
EFLOWDOWN  = 1005  # Flow is down
EFLOWPEER  = 1006  # Flow is down (peer timed out)
ENAME      = 1007  # Naming error
ECRYPT     = 1008  # Encryption error
EAUTH      = 1009  # Authentication error
EREPLAY    = 1010  # OAP replay detected

_O7S_ERRNO_STR: dict[int, str] = {
    ENOTALLOC:  "flow is not allocated",
    EIPCPTYPE:  "unknown IPCP type",
    EIRMD:      "failed to communicate with IRMd",
    EIPCP:      "failed to communicate with IPCP",
    EIPCPSTATE: "target in wrong state",
    EFLOWDOWN:  "flow is down",
    EFLOWPEER:  "flow peer timed out",
    ENAME:      "naming error",
    ECRYPT:     "encryption error",
    EAUTH:      "authentication error",
    EREPLAY:    "OAP replay detected",
}


class OuroborosError(Exception):
    """
    Base class for all pyouroboros exceptions.
    """


class IrmError(OuroborosError):
    """
    Base class for IRM (control plane) errors.
    """


class IpcpCreateError(IrmError):
    """
    Raised when IPCP creation fails.
    """


class IpcpBootstrapError(IrmError):
    """
    Raised when IPCP bootstrapping fails.
    """


class IpcpEnrollError(IrmError):
    """
    Raised when IPCP enrollment fails.
    """


class IpcpConnectError(IrmError):
    """
    Raised when IPCP connection or disconnection fails.
    """


class IpcpTypeError(IrmError, ValueError):
    """
    Raised when an unknown IPCP type is encountered.
    """


class IpcpStateError(IrmError):
    """
    Raised when an IPCP/IRMd is in the wrong state for the request.
    """


class IrmdError(IrmError):
    """
    Raised when the IRM daemon is unreachable.
    """


class IpcpdError(IrmError):
    """
    Raised when the IPCP daemon is unreachable.
    """


class BindError(IrmError):
    """
    Raised when binding a program/process/IPCP to a name fails.
    """


class NameNotFoundError(IrmError):
    """
    Raised when a name lookup or unregister target is missing.
    """


class NameExistsError(IrmError):
    """
    Raised when a name already exists.
    """


class InvalidNameError(IrmError, ValueError):
    """
    Raised when a name is malformed or otherwise invalid.
    """


class FlowError(OuroborosError):
    """
    Base class for flow-plane errors.
    """


class FlowAlreadyAllocatedError(FlowError):
    """
    Raised when allocating on a Flow that already holds an fd.
    """


class FlowNotAllocatedError(FlowError):
    """
    Raised when operating on a Flow that has no fd.
    """


class FlowDownError(FlowError, ConnectionError):
    """
    Raised when the flow has gone down.
    """


class FlowPeerError(FlowDownError):
    """
    Raised when the flow's peer has timed out.
    """


class FlowPermissionError(FlowError, PermissionError):
    """
    Raised when an operation is not permitted on the flow.
    """


class FlowTimeout(FlowError, TimeoutError):
    """
    Raised when a flow operation times out.
    """


class FlowCryptError(FlowError):
    """
    Raised on flow encryption errors.
    """


class FlowAuthError(FlowError):
    """
    Raised on flow authentication errors.
    """


class FlowReplayError(FlowError):
    """
    Raised when OAP replay is detected.
    """


class FlowEventError(FlowError):
    """
    Raised on errors from the flow event subsystem.
    """


class FlowDeallocWarning(Warning):
    """
    Warning issued when a deallocation reports a non-fatal problem.
    """


_ERRNO_MAP: dict[int, type[BaseException]] = {
    errno.ETIMEDOUT:    TimeoutError,
    errno.EAGAIN:       BlockingIOError,
    errno.EWOULDBLOCK:  BlockingIOError,
    errno.ENOMEM:       MemoryError,
    errno.EACCES:       PermissionError,
    errno.ENOTCONN:     ConnectionError,
    errno.ECONNRESET:   ConnectionResetError,
    ENOTALLOC:          FlowNotAllocatedError,
    EIPCPTYPE:          IpcpTypeError,
    EIRMD:              IrmdError,
    EIPCP:              IpcpdError,
    EIPCPSTATE:         IpcpStateError,
    EFLOWDOWN:          FlowDownError,
    EFLOWPEER:          FlowPeerError,
    ENAME:              NameNotFoundError,
    ECRYPT:             FlowCryptError,
    EAUTH:              FlowAuthError,
    EREPLAY:            FlowReplayError,
}


def _strerror(err: int) -> str:
    if err >= 1000:
        return _O7S_ERRNO_STR.get(err, f"ouroboros errno {err}")

    return os.strerror(err)


def raise_errno(rc: int, default: type[OuroborosError] = FlowError) -> int:
    """
    Translate a non-negative-or-negative-errno return code.

    ``_ERRNO_MAP`` holds errnos in their canonical positive form.

    :param rc:              The return code to translate; a negative
                            value is a negated errno.
    :param default:         Exception class to raise when the errno
                            has no mapping; a mapped errno overrides
                            it.
    :return:                *rc* unchanged when it is non-negative.
    :raises OuroborosError: (or the builtin mapped for ``-rc``) when
                            *rc* is negative.
    """

    if rc >= 0:
        return rc

    err = -rc
    exc_cls = _ERRNO_MAP.get(err, default)
    raise exc_cls(_strerror(err))


def check_ouroboros_version(o7s_major: int, o7s_minor: int) -> None:
    """
    Verify that the installed pyouroboros matches the linked library.

    Compares the linked library version against the installed
    pyouroboros distribution metadata. Silently returns when running
    from a source tree without distribution metadata.

    :param o7s_major:     Major version of the linked library, from
                          ``OUROBOROS_VERSION_MAJOR`` in the CFFI
                          module.
    :param o7s_minor:     Minor version of the linked library, from
                          ``OUROBOROS_VERSION_MINOR`` in the CFFI
                          module.
    :raises RuntimeError: If the library and pyouroboros ``major.minor``
                          differ.
    """

    try:
        pyo7s_parts = version("PyOuroboros").split(".")
    except PackageNotFoundError:
        return

    if o7s_major != int(pyo7s_parts[0]) or \
            o7s_minor != int(pyo7s_parts[1]):
        raise RuntimeError(
            f"Ouroboros version mismatch: library is "
            f"{o7s_major}.{o7s_minor}, pyouroboros is "
            f"{pyo7s_parts[0]}.{pyo7s_parts[1]}"
        )
