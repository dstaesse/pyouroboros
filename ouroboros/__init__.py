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

"""Public Python API for Ouroboros.

The package surface only re-exports pure-Python helpers (errors and
QoS).  Applications import the load-bearing parts of the API from
their submodule explicitly: flows from :mod:`ouroboros.dev`, the
event loop from :mod:`ouroboros.event`, and the control plane from
:mod:`ouroboros.irm` (or :mod:`ouroboros.cli`).  Submodule paths
make the caller's intent explicit and keep the package importable
in environments that have no business loading the libouroboros CFFI
extensions (see ``CLAUDE.md`` for the underlying init-on-load
behaviour that makes this contract load-bearing in practice).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from ouroboros.errors import (
    BindError,
    FlowAuthError,
    FlowCryptError,
    FlowDeallocWarning,
    FlowDownError,
    FlowError,
    FlowEventError,
    FlowPeerError,
    FlowPermissionError,
    FlowReplayError,
    InvalidNameError,
    IpcpBootstrapError,
    IpcpConnectError,
    IpcpCreateError,
    IpcpEnrollError,
    IpcpStateError,
    IpcpTypeError,
    IpcpdError,
    IrmError,
    IrmdError,
    NameExistsError,
    NameNotFoundError,
    OuroborosError,
)
from ouroboros.qos import (
    QOS_MSG,
    QOS_RAW,
    QOS_RAW_SAFE,
    QOS_RT,
    QOS_RT_SAFE,
    QOS_STREAM,
    QoSService,
    QoSSpec,
)

try:
    __version__ = version("PyOuroboros")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "__version__",
    # qos
    "QoSService", "QoSSpec",
    "QOS_MSG", "QOS_RAW", "QOS_RAW_SAFE",
    "QOS_RT", "QOS_RT_SAFE", "QOS_STREAM",
    # errors
    "OuroborosError",
    "IrmError", "IrmdError", "IpcpdError",
    "IpcpCreateError", "IpcpBootstrapError", "IpcpEnrollError",
    "IpcpConnectError", "IpcpTypeError", "IpcpStateError",
    "BindError",
    "NameNotFoundError", "NameExistsError", "InvalidNameError",
    "FlowError", "FlowDownError", "FlowPeerError",
    "FlowPermissionError", "FlowEventError",
    "FlowCryptError", "FlowAuthError", "FlowReplayError",
    "FlowDeallocWarning",
]
