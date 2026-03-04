#
# Ouroboros - Copyright (C) 2016 - 2026
#
# Python API for Ouroboros - CLI equivalents
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

"""
Higher-level wrappers that mirror CLI tool behaviour.

The ``irm`` CLI tools perform extra steps that the raw C library API
does not, such as resolving program names via ``realpath``, looking up
IPCP pids, and the ``autobind`` flag for bootstrapping/enrolling.
This module exposes those same patterns as a Python API so that
callers do not need to re-implement them.

Each wrapper corresponds to a specific ``irm`` sub-command:

=========================  ====================================
Python                     CLI equivalent
=========================  ====================================
``create_ipcp``            ``irm ipcp create``
``destroy_ipcp``           ``irm ipcp destroy``
``bootstrap_ipcp``         ``irm ipcp bootstrap [autobind]``
``enroll_ipcp``            ``irm ipcp enroll [autobind]``
``connect_ipcp``           ``irm ipcp connect``
``disconnect_ipcp``        ``irm ipcp disconnect``
``list_ipcps``             ``irm ipcp list``
``bind_program``           ``irm bind program``
``bind_process``           ``irm bind process``
``bind_ipcp``              ``irm bind ipcp``
``unbind_program``         ``irm unbind program``
``unbind_process``         ``irm unbind process``
``unbind_ipcp``            ``irm unbind ipcp``
``create_name``            ``irm name create``
``destroy_name``           ``irm name destroy``
``reg_name``               ``irm name register``
``unreg_name``             ``irm name unregister``
``list_names``             ``irm name list``
``autoboot``               ``irm ipcp bootstrap autobind``
                           (with implicit ``create``)
=========================  ====================================

Usage::

    from ouroboros.cli import create_ipcp, bootstrap_ipcp, enroll_ipcp
    from ouroboros.cli import bind_program, autoboot
"""

import shutil
from typing import List, Optional

from ouroboros.irm import (
    DT_COMP,
    MGMT_COMP,
    IpcpType,
    IpcpConfig,
    IpcpInfo,
    NameInfo,
    BindError,
    IrmError,
    UnicastConfig,
    DtConfig,
    RoutingConfig,
    LinkStateConfig,
    LinkStatePolicy,
    EthConfig,
    Udp4Config,
    Udp6Config,
    bind_program as _irm_bind_program,
    bind_process as _irm_bind_process,
    bootstrap_ipcp as _irm_bootstrap_ipcp,
    connect_ipcp as _irm_connect_ipcp,
    create_ipcp,
    create_name as _irm_create_name,
    destroy_ipcp as _irm_destroy_ipcp,
    destroy_name,
    disconnect_ipcp as _irm_disconnect_ipcp,
    enroll_ipcp as _irm_enroll_ipcp,
    list_ipcps as _irm_list_ipcps,
    list_names as _irm_list_names,
    reg_name as _irm_reg_name,
    unbind_process as _irm_unbind_process,
    unbind_program as _irm_unbind_program,
    unreg_name as _irm_unreg_name,
)
from ouroboros.qos import QoSSpec


def _pid_of(ipcp_name: str) -> int:
    """Look up the pid of a running IPCP by its name."""
    for info in _irm_list_ipcps():
        if info.name == ipcp_name:
            return info.pid
    raise ValueError(f"No IPCP named {ipcp_name!r}")


def destroy_ipcp(name: str) -> None:
    """
    Destroy an IPCP by name.

    Mirrors ``irm ipcp destroy name <name>``.

    Resolves the IPCP name to a pid, then destroys the IPCP.

    :param name: Name of the IPCP to destroy.
    :raises ValueError: If no IPCP with *name* exists.
    """
    _irm_destroy_ipcp(_pid_of(name))


def list_ipcps(name: Optional[str] = None,
               layer: Optional[str] = None,
               ipcp_type: Optional[IpcpType] = None) -> List[IpcpInfo]:
    """
    List running IPCPs, optionally filtered.

    Mirrors ``irm ipcp list [name <n>] [type <t>] [layer <l>]``.

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


def reg_name(name: str,
             ipcp: Optional[str] = None,
             ipcps: Optional[List[str]] = None,
             layer: Optional[str] = None,
             layers: Optional[List[str]] = None) -> None:
    """
    Register a name with IPCP(s), creating it first if needed.

    Mirrors ``irm name register <name> ipcp <ipcp> [ipcp ...]
    layer <layer> [layer ...]``.

    The C CLI tool resolves IPCP names and layer names to pids,
    checks whether the name already exists and calls
    ``irm_create_name`` before ``irm_reg_name`` for each IPCP.

    The function accepts flexible input:

    - A single *ipcp* name or list of *ipcps* names.
    - A single *layer* name or list of *layers* names (registers
      with every IPCP in each of those layers).
    - Any combination of the above.

    :param name:   The name to register.
    :param ipcp:   Single IPCP name to register with.
    :param ipcps:  List of IPCP names to register with.
    :param layer:  Single layer name to register with.
    :param layers: List of layer names to register with.
    """
    existing = {n.name for n in _irm_list_names()}
    if name not in existing:
        _irm_create_name(NameInfo(name=name))

    pids = set()

    # Collect IPCP names into a single list
    ipcp_names = []
    if ipcp is not None:
        ipcp_names.append(ipcp)
    if ipcps is not None:
        ipcp_names.extend(ipcps)

    # Collect layer names into a single list
    layer_names = []
    if layer is not None:
        layer_names.append(layer)
    if layers is not None:
        layer_names.extend(layers)

    if ipcp_names or layer_names:
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

    for p in pids:
        _irm_reg_name(name, p)


def bind_program(prog: str,
                 name: str,
                 opts: int = 0,
                 argv: Optional[List[str]] = None) -> None:
    """
    Bind a program to a name, resolving bare names to full paths.

    Mirrors ``irm bind program <prog> name <name>``.

    The ``irm bind program`` CLI tool calls ``realpath()`` on *prog*
    before passing it to the library.  The raw C function
    ``irm_bind_program`` contains a ``check_prog_path`` helper that
    corrupts the ``PATH`` environment variable (writes NUL over ``:``
    separators) when given a bare program name.  Only the first such
    call would succeed in a long-running process.

    This wrapper resolves *prog* via ``shutil.which()`` before calling
    the library, avoiding the bug entirely.

    :param prog: Program name or path.  Bare names (without ``/``)
                 are resolved on ``PATH`` via ``shutil.which()``.
    :param name: Name to bind to.
    :param opts: Bind options (e.g. ``BIND_AUTO``).
    :param argv: Arguments to pass when the program is auto-started.
    :raises BindError: If the program cannot be found or the bind
                       call fails.
    """
    if '/' not in prog:
        resolved = shutil.which(prog)
        if resolved is None:
            raise BindError(f"Program {prog!r} not found on PATH")
        prog = resolved
    _irm_bind_program(prog, name, opts=opts, argv=argv)


def unbind_program(prog: str, name: str) -> None:
    """
    Unbind a program from a name.

    Mirrors ``irm unbind program <prog> name <name>``.

    :param prog: Path to the program.
    :param name: Name to unbind from.
    """
    _irm_unbind_program(prog, name)


def bind_process(pid: int, name: str) -> None:
    """
    Bind a running process to a name.

    Mirrors ``irm bind process <pid> name <name>``.

    :param pid:  PID of the process.
    :param name: Name to bind to.
    """
    _irm_bind_process(pid, name)


def unbind_process(pid: int, name: str) -> None:
    """
    Unbind a process from a name.

    Mirrors ``irm unbind process <pid> name <name>``.

    :param pid:  PID of the process.
    :param name: Name to unbind from.
    """
    _irm_unbind_process(pid, name)


def bind_ipcp(ipcp: str, name: str) -> None:
    """
    Bind an IPCP to a name.

    Mirrors ``irm bind ipcp <ipcp> name <name>``.

    Resolves the IPCP name to a pid, then calls ``bind_process``.

    :param ipcp: IPCP instance name.
    :param name: Name to bind to.
    :raises ValueError: If no IPCP with *ipcp* exists.
    """
    _irm_bind_process(_pid_of(ipcp), name)


def unbind_ipcp(ipcp: str, name: str) -> None:
    """
    Unbind an IPCP from a name.

    Mirrors ``irm unbind ipcp <ipcp> name <name>``.

    Resolves the IPCP name to a pid, then calls ``unbind_process``.

    :param ipcp: IPCP instance name.
    :param name: Name to unbind from.
    :raises ValueError: If no IPCP with *ipcp* exists.
    """
    _irm_unbind_process(_pid_of(ipcp), name)


def create_name(name: str,
                pol_lb: Optional[int] = None,
                info: Optional[NameInfo] = None) -> None:
    """
    Create a registered name.

    Mirrors ``irm name create <name> [lb <policy>]``.

    :param name:   The name to create.
    :param pol_lb: Load-balance policy (optional).
    :param info:   Full :class:`NameInfo` (overrides *name*/*pol_lb*
                   if given).
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
    List all registered names, optionally filtered.

    Mirrors ``irm name list [<name>]``.

    :param name: Filter by name (exact match).
    :return:     List of :class:`NameInfo` objects.
    """
    result = _irm_list_names()
    if name is not None:
        result = [n for n in result if n.name == name]
    return result


def unreg_name(name: str,
               ipcp: Optional[str] = None,
               ipcps: Optional[List[str]] = None,
               layer: Optional[str] = None,
               layers: Optional[List[str]] = None) -> None:
    """
    Unregister a name from IPCP(s).

    Mirrors ``irm name unregister <name> ipcp <ipcp> [ipcp ...]
    layer <layer> [layer ...]``.

    Accepts the same flexible input as :func:`reg_name`.

    :param name:   The name to unregister.
    :param ipcp:   Single IPCP name to unregister from.
    :param ipcps:  List of IPCP names to unregister from.
    :param layer:  Single layer name to unregister from.
    :param layers: List of layer names to unregister from.
    """
    pids = set()

    ipcp_names = []
    if ipcp is not None:
        ipcp_names.append(ipcp)
    if ipcps is not None:
        ipcp_names.extend(ipcps)

    layer_names = []
    if layer is not None:
        layer_names.append(layer)
    if layers is not None:
        layer_names.extend(layers)

    if ipcp_names or layer_names:
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

    for p in pids:
        _irm_unreg_name(name, p)


def bootstrap_ipcp(name: str,
                   conf: IpcpConfig,
                   autobind: bool = False) -> None:
    """
    Bootstrap an IPCP, optionally binding it to its name and layer.

    Mirrors ``irm ipcp bootstrap name <n> layer <l> [autobind]``.

    When *autobind* is ``True`` and the IPCP type is ``UNICAST`` or
    ``BROADCAST``, the sequence is::

        bind_process(pid, ipcp_name)    # accept flows for ipcp name
        bind_process(pid, layer_name)   # accept flows for layer name
        bootstrap_ipcp(pid, conf)       # bootstrap into the layer

    This matches the C ``irm ipcp bootstrap`` tool exactly.  If
    bootstrap fails after autobind, the bindings are rolled back.

    :param name:     Name of the IPCP.
    :param conf:     IPCP configuration (includes layer name & type).
    :param autobind: Bind the IPCP process to its name and layer.
    """
    pid = _pid_of(name)
    layer_name = conf.layer_name

    if autobind and conf.ipcp_type in (IpcpType.UNICAST,
                                       IpcpType.BROADCAST):
        _irm_bind_process(pid, name)
        _irm_bind_process(pid, layer_name)

    try:
        _irm_bootstrap_ipcp(pid, conf)
    except Exception:
        if autobind and conf.ipcp_type in (IpcpType.UNICAST,
                                           IpcpType.BROADCAST):
            _irm_unbind_process(pid, name)
            _irm_unbind_process(pid, layer_name)
        raise


def enroll_ipcp(name: str, dst: str,
                autobind: bool = False) -> None:
    """
    Enroll an IPCP, optionally binding it to its name and layer.

    Mirrors ``irm ipcp enroll name <n> layer <dst> [autobind]``.

    When *autobind* is ``True``, the sequence is::

        enroll_ipcp(pid, dst)
        bind_process(pid, ipcp_name)
        bind_process(pid, layer_name)  # layer learned from enrollment

    This matches the C ``irm ipcp enroll`` tool exactly.

    :param name:     Name of the IPCP.
    :param dst:      Destination name or layer to enroll with.
    :param autobind: Bind the IPCP process to its name and layer
                     after successful enrollment.
    """
    pid = _pid_of(name)
    _irm_enroll_ipcp(pid, dst)

    if autobind:
        # Look up enrolled layer from the IPCP list
        for info in _irm_list_ipcps():
            if info.pid == pid:
                _irm_bind_process(pid, info.name)
                _irm_bind_process(pid, info.layer)
                break


def connect_ipcp(name: str, dst: str, comp: str = "*",
                 qos: Optional[QoSSpec] = None) -> None:
    """
    Connect IPCP components to a destination.

    Mirrors ``irm ipcp connect name <n> dst <dst> [component <c>]
    [qos <qos>]``.

    When *comp* is ``"*"`` (default), both ``dt`` and ``mgmt``
    components are connected, matching the CLI default.

    :param name: Name of the IPCP.
    :param dst:  Destination IPCP name.
    :param comp: Component to connect: ``"dt"``, ``"mgmt"``, or
                 ``"*"`` for both (default).
    :param qos:  QoS specification for the dt component.
    """
    pid = _pid_of(name)
    if comp in ("*", "mgmt"):
        _irm_connect_ipcp(pid, MGMT_COMP, dst)
    if comp in ("*", "dt"):
        _irm_connect_ipcp(pid, DT_COMP, dst, qos=qos)


def disconnect_ipcp(name: str, dst: str, comp: str = "*") -> None:
    """
    Disconnect IPCP components from a destination.

    Mirrors ``irm ipcp disconnect name <n> dst <dst>
    [component <c>]``.

    When *comp* is ``"*"`` (default), both ``dt`` and ``mgmt``
    components are disconnected, matching the CLI default.

    :param name: Name of the IPCP.
    :param dst:  Destination IPCP name.
    :param comp: Component to disconnect: ``"dt"``, ``"mgmt"``, or
                 ``"*"`` for both (default).
    """
    pid = _pid_of(name)
    if comp in ("*", "mgmt"):
        _irm_disconnect_ipcp(pid, MGMT_COMP, dst)
    if comp in ("*", "dt"):
        _irm_disconnect_ipcp(pid, DT_COMP, dst)


def autoboot(name: str,
             ipcp_type: IpcpType,
             layer: str,
             conf: Optional[IpcpConfig] = None) -> None:
    """
    Create, autobind and bootstrap an IPCP in one step.

    Convenience wrapper equivalent to::

        irm ipcp bootstrap name <name> type <type> layer <layer> autobind

    (with an implicit ``create`` if the IPCP does not yet exist).

    :param name:      Name for the IPCP.
    :param ipcp_type: Type of IPCP to create.
    :param layer:     Layer name to bootstrap into.
    :param conf:      Optional IPCP configuration.  If *None*, a
                      default ``IpcpConfig`` is created for the given
                      *ipcp_type* and *layer*.
    """
    create_ipcp(name, ipcp_type)
    if conf is None:
        conf = IpcpConfig(ipcp_type=ipcp_type, layer_name=layer)
    else:
        conf.layer_name = layer
    bootstrap_ipcp(name, conf, autobind=True)
