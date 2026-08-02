#
# SPDX-FileCopyrightText: 2016 - 2026 Dimitri Staessens
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Public Python API for Ouroboros.

The package surface re-exports the pure-Python helpers only: errors and
QoS. The rest of the API is imported from its submodule: flows from
:mod:`ouroboros.dev`, the event loop from :mod:`ouroboros.event`, the
control plane from :mod:`ouroboros.irm` (or :mod:`ouroboros.cli`).
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
    IpcpAttachError,
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
    "QoSService",
    "QoSSpec",
    "QOS_MSG",
    "QOS_RAW",
    "QOS_RAW_SAFE",
    "QOS_RT",
    "QOS_RT_SAFE",
    "QOS_STREAM",
    # errors
    "OuroborosError",
    "IrmError",
    "IrmdError",
    "IpcpdError",
    "IpcpCreateError",
    "IpcpBootstrapError",
    "IpcpAttachError",
    "IpcpEnrollError",
    "IpcpConnectError",
    "IpcpTypeError",
    "IpcpStateError",
    "BindError",
    "NameNotFoundError",
    "NameExistsError",
    "InvalidNameError",
    "FlowError",
    "FlowDownError",
    "FlowPeerError",
    "FlowPermissionError",
    "FlowEventError",
    "FlowCryptError",
    "FlowAuthError",
    "FlowReplayError",
    "FlowDeallocWarning",
]
