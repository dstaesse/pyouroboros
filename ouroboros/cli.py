#
# SPDX-FileCopyrightText: 2016 - 2026 Dimitri Staessens
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Higher-level wrappers that mirror the ``irm`` CLI tool behaviour.

Adds program path resolution, IPCP name-to-pid lookup and ``autobind``
handling on top of the raw IRM API.
"""

from __future__ import annotations

import shutil
from typing import List, Optional, Set

from ouroboros.errors import BindError
from ouroboros.irm import (
    DT_COMP,
    MGMT_COMP,
    DhtConfig,
    DirConfig,
    DtConfig,
    EthPoa,
    IpcpConfig,
    IpcpInfo,
    IpcpType,
    LinkStateConfig,
    NameInfo,
    PoaAddr,
    PoaSpec,
    PoaType,
    RoutingConfig,
    Udp4Poa,
    Udp6Poa,
    UnicastConfig,
    attach_ipcp as _irm_attach_ipcp,
    bind_program as _irm_bind_program,
    bind_process as _irm_bind_process,
    bootstrap_ipcp as _irm_bootstrap_ipcp,
    connect_ipcp as _irm_connect_ipcp,
    create_ipcp,
    create_name as _irm_create_name,
    destroy_ipcp as _irm_destroy_ipcp,
    destroy_name,
    detach_ipcp as _irm_detach_ipcp,
    disconnect_ipcp as _irm_disconnect_ipcp,
    enroll_ipcp as _irm_enroll_ipcp,
    list_ipcps as _irm_list_ipcps,
    list_names as _irm_list_names,
    list_poas as _irm_list_poas,
    reg_name as _irm_reg_name,
    unbind_process as _irm_unbind_process,
    unbind_program as _irm_unbind_program,
    unreg_name as _irm_unreg_name,
)
from ouroboros.qos import QoSSpec

__all__ = [
    # Functions
    "create_ipcp",
    "destroy_ipcp",
    "bootstrap_ipcp",
    "attach_ipcp",
    "detach_ipcp",
    "list_poas",
    "enroll_ipcp",
    "connect_ipcp",
    "disconnect_ipcp",
    "list_ipcps",
    "bind_program",
    "bind_process",
    "bind_ipcp",
    "unbind_program",
    "unbind_process",
    "unbind_ipcp",
    "create_name",
    "destroy_name",
    "reg_name",
    "unreg_name",
    "list_names",
    "autoboot",
    # Re-exported configuration types
    "DhtConfig",
    "DirConfig",
    "DtConfig",
    "EthPoa",
    "IpcpConfig",
    "IpcpInfo",
    "IpcpType",
    "LinkStateConfig",
    "NameInfo",
    "PoaAddr",
    "PoaSpec",
    "PoaType",
    "RoutingConfig",
    "Udp4Poa",
    "Udp6Poa",
    "UnicastConfig",
]


def _pid_of(ipcp_name: str) -> int:
    """
    Look up the pid of a running IPCP by its name.
    """

    for info in _irm_list_ipcps():
        if info.name == ipcp_name:
            return info.pid

    raise ValueError(f"No IPCP named {ipcp_name!r}")


def _collect_pids(
    ipcp: Optional[str],
    ipcps: Optional[List[str]],
    layer: Optional[str],
    layers: Optional[List[str]],
) -> Set[int]:
    """
    Collect the set of pids matching the given name/layer filters.
    """

    ipcp_names: List[str] = []

    if ipcp is not None:
        ipcp_names.append(ipcp)

    if ipcps is not None:
        ipcp_names.extend(ipcps)

    layer_names: List[str] = []

    if layer is not None:
        layer_names.append(layer)

    if layers is not None:
        layer_names.extend(layers)

    pids: Set[int] = set()

    if not ipcp_names and not layer_names:
        return pids

    all_ipcps = _irm_list_ipcps()

    for ipcp_name in ipcp_names:
        for i in all_ipcps:
            if i.name == ipcp_name:
                pids.add(i.pid)
                break

    for lyr in layer_names:
        for i in all_ipcps:
            if i.layer == lyr:
                pids.add(i.pid)

    return pids


def destroy_ipcp(name: str) -> None:
    """
    Destroy an IPCP by name.

    :param name: Name of the IPCP to destroy.
    :raises ValueError: If no IPCP with *name* exists.
    """

    _irm_destroy_ipcp(_pid_of(name))


def list_ipcps(
    name: Optional[str] = None, layer: Optional[str] = None, ipcp_type: Optional[IpcpType] = None
) -> List[IpcpInfo]:
    """
    List running IPCPs, optionally filtered.

    Filters are exact matches.

    :param name:      Filter by IPCP name (exact match).
    :param layer:     Filter by layer name (exact match).
    :param ipcp_type: Filter by IPCP type.
    :return:          List of matching :class:`IpcpInfo` objects.
    """

    result = _irm_list_ipcps()

    if name is not None:
        result = [i for i in result if i.name == name]

    if layer is not None:
        result = [i for i in result if i.layer == layer]

    if ipcp_type is not None:
        result = [i for i in result if i.type == ipcp_type]

    return result


def reg_name(
    name: str,
    ipcp: Optional[str] = None,
    ipcps: Optional[List[str]] = None,
    layer: Optional[str] = None,
    layers: Optional[List[str]] = None,
) -> None:
    """
    Register a name with IPCP(s), creating it first if needed.

    Registers with every IPCP in *layer* and *layers*.

    :param name:   The name to register.
    :param ipcp:   Single IPCP name to register with.
    :param ipcps:  List of IPCP names to register with.
    :param layer:  Single layer name to register with.
    :param layers: List of layer names to register with.
    """

    existing = {n.name for n in _irm_list_names()}
    if name not in existing:
        _irm_create_name(NameInfo(name=name))

    for pid in _collect_pids(ipcp, ipcps, layer, layers):
        _irm_reg_name(name, pid)


def bind_program(prog: str, name: str, opts: int = 0, argv: Optional[List[str]] = None) -> None:
    """
    Bind a program to a name.

    :param prog: Program name or path. Bare names (without ``/``) are
                 resolved on ``PATH``.
    :param name: Name to bind to.
    :param opts: Bind options (e.g. ``BIND_AUTO``).
    :param argv: Arguments passed when the program is auto-started.
    :raises BindError: If the program is not found on ``PATH``.
    """

    if "/" not in prog:
        resolved = shutil.which(prog)
        if resolved is None:
            raise BindError(f"Program {prog!r} not found on PATH")

        prog = resolved

    _irm_bind_program(prog, name, opts=opts, argv=argv)


def unbind_program(prog: str, name: str) -> None:
    """
    Unbind a program from a name.

    :param prog: Path to the program.
    :param name: Name to unbind from.
    """

    _irm_unbind_program(prog, name)


def bind_process(pid: int, name: str) -> None:
    """
    Bind a running process to a name.

    :param pid:  PID of the process.
    :param name: Name to bind to.
    """

    _irm_bind_process(pid, name)


def unbind_process(pid: int, name: str) -> None:
    """
    Unbind a process from a name.

    :param pid:  PID of the process.
    :param name: Name to unbind from.
    """

    _irm_unbind_process(pid, name)


def bind_ipcp(ipcp: str, name: str) -> None:
    """
    Bind an IPCP to a name.

    :param ipcp: IPCP instance name.
    :param name: Name to bind to.
    :raises ValueError: If no IPCP with *ipcp* exists.
    """

    _irm_bind_process(_pid_of(ipcp), name)


def unbind_ipcp(ipcp: str, name: str) -> None:
    """
    Unbind an IPCP from a name.

    :param ipcp: IPCP instance name.
    :param name: Name to unbind from.
    :raises ValueError: If no IPCP with *ipcp* exists.
    """

    _irm_unbind_process(_pid_of(ipcp), name)


def create_name(name: str, pol_lb: Optional[int] = None, info: Optional[NameInfo] = None) -> None:
    """
    Create a registered name.

    :param name:   The name to create.
    :param pol_lb: Load-balance policy.
    :param info:   Full :class:`NameInfo`; overrides *name* and
                   *pol_lb*.
    """

    if info is not None:
        _irm_create_name(info)
    else:
        ni = NameInfo(name=name)

        if pol_lb is not None:
            ni.pol_lb = pol_lb

        _irm_create_name(ni)


def list_names(name: Optional[str] = None) -> List[NameInfo]:
    """
    List all registered names, optionally filtered on exact name.

    :param name: Filter by name (exact match).
    :return:     List of :class:`NameInfo` objects.
    """

    result = _irm_list_names()

    if name is not None:
        result = [n for n in result if n.name == name]

    return result


def unreg_name(
    name: str,
    ipcp: Optional[str] = None,
    ipcps: Optional[List[str]] = None,
    layer: Optional[str] = None,
    layers: Optional[List[str]] = None,
) -> None:
    """
    Unregister a name from IPCP(s).

    Unregisters from every IPCP in *layer* and *layers*.

    :param name:   The name to unregister.
    :param ipcp:   Single IPCP name to unregister from.
    :param ipcps:  List of IPCP names to unregister from.
    :param layer:  Single layer name to unregister from.
    :param layers: List of layer names to unregister from.
    """

    for pid in _collect_pids(ipcp, ipcps, layer, layers):
        _irm_unreg_name(name, pid)


def bootstrap_ipcp(name: str, conf: IpcpConfig, autobind: bool = False) -> None:
    """
    Bootstrap an IPCP, optionally binding it to its name and layer.

    Autobind applies to UNICAST and BROADCAST IPCPs only, and is rolled
    back if the bootstrap fails.

    :param name:     Name of the IPCP.
    :param conf:     IPCP configuration, including layer name and type.
    :param autobind: Bind the IPCP process to its name and layer.
    """

    pid = _pid_of(name)
    layer_name = conf.layer_name

    autobind_types = (IpcpType.UNICAST, IpcpType.BROADCAST)
    if autobind and conf.ipcp_type in autobind_types:
        _irm_bind_process(pid, name)
        _irm_bind_process(pid, layer_name)

    try:
        _irm_bootstrap_ipcp(pid, conf)
    except Exception:
        if autobind and conf.ipcp_type in autobind_types:
            _irm_unbind_process(pid, name)
            _irm_unbind_process(pid, layer_name)

        raise


def attach_ipcp(name: str, poa: PoaSpec) -> None:
    """
    Attach an IPCP to a medium. Repeat for more than one PoA.

    :param name: Name of the IPCP.
    :param poa:  The PoA to attach to.
    """

    _irm_attach_ipcp(_pid_of(name), poa)


def detach_ipcp(name: str, poa: PoaSpec) -> None:
    """
    Release a PoA an IPCP is attached to.

    :param name: Name of the IPCP.
    :param poa:  The PoA to release.
    """

    _irm_detach_ipcp(_pid_of(name), poa)


def list_poas(name: str) -> List[PoaSpec]:
    """
    List the PoAs an IPCP is attached to.

    :param name: Name of the IPCP.
    :return:     List of :class:`PoaSpec` objects.
    """

    return _irm_list_poas(_pid_of(name))


def enroll_ipcp(
    name: str, dst: str, autobind: bool = False, addr: Optional[PoaAddr] = None
) -> None:
    """
    Enroll an IPCP, optionally binding it to its name and layer.

    The IPCP must already be attached to a PoA that can reach
    *addr*; see :func:`attach_ipcp`.

    :param name:     Name of the IPCP.
    :param dst:      Destination name or layer to enroll with.
    :param autobind: Bind the IPCP process to its name and to the layer
                     learned during enrollment.
    :param addr:     Address of the PoA to enroll over.
    """

    pid = _pid_of(name)

    _irm_enroll_ipcp(pid, dst, addr=addr)

    if autobind:
        for info in _irm_list_ipcps():
            if info.pid == pid:
                _irm_bind_process(pid, info.name)
                _irm_bind_process(pid, info.layer)
                break


def connect_ipcp(
    name: str,
    dst: str,
    comp: str = "*",
    qos: Optional[QoSSpec] = None,
    addr: Optional[PoaAddr] = None,
) -> None:
    """
    Connect IPCP components to a destination.

    :param name: Name of the IPCP.
    :param dst:  Destination IPCP name.
    :param comp: ``"dt"``, ``"mgmt"``, or ``"*"`` for both.
    :param qos:  QoS specification for the dt component.
    :param addr: Address of the PoA to connect over.
    """

    pid = _pid_of(name)

    if comp in ("*", "mgmt"):
        _irm_connect_ipcp(pid, MGMT_COMP, dst, addr=addr)

    if comp in ("*", "dt"):
        _irm_connect_ipcp(pid, DT_COMP, dst, qos=qos, addr=addr)


def disconnect_ipcp(name: str, dst: str, comp: str = "*") -> None:
    """
    Disconnect IPCP components from a destination.

    :param name: Name of the IPCP.
    :param dst:  Destination IPCP name.
    :param comp: ``"dt"``, ``"mgmt"``, or ``"*"`` for both.
    """

    pid = _pid_of(name)

    if comp in ("*", "mgmt"):
        _irm_disconnect_ipcp(pid, MGMT_COMP, dst)

    if comp in ("*", "dt"):
        _irm_disconnect_ipcp(pid, DT_COMP, dst)


def autoboot(name: str, ipcp_type: IpcpType, layer: str, conf: Optional[IpcpConfig] = None) -> None:
    """
    Create, autobind and bootstrap an IPCP in one step.

    :param name:      Name for the IPCP.
    :param ipcp_type: Type of IPCP to create.
    :param layer:     Layer name to bootstrap into.
    :param conf:      IPCP configuration. If *None*, a default
                      :class:`IpcpConfig` is built from *ipcp_type* and
                      *layer*.
    """

    create_ipcp(name, ipcp_type)

    if conf is None:
        conf = IpcpConfig(ipcp_type=ipcp_type, layer_name=layer)
    else:
        conf.layer_name = layer

    bootstrap_ipcp(name, conf, autobind=True)
