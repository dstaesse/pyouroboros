#
# SPDX-FileCopyrightText: 2016 - 2026 Dimitri Staessens
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
IRM (IPC Resource Manager) bindings for Ouroboros.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, List, Optional

from _ouroboros_irm_cffi import ffi, lib

from ouroboros._qosspec import qos_to_qosspec
from ouroboros.errors import (
    BindError,
    IpcpAttachError,
    IpcpBootstrapError,
    IpcpConnectError,
    IpcpCreateError,
    IpcpEnrollError,
    IrmError,
    NameExistsError,
    NameNotFoundError,
    check_ouroboros_version,
    raise_errno,
)
from ouroboros.qos import QoSSpec

check_ouroboros_version(lib.OUROBOROS_VERSION_MAJOR, lib.OUROBOROS_VERSION_MINOR)

BIND_AUTO = lib.BIND_AUTO

DT_COMP = "Data Transfer"
MGMT_COMP = "Management"


class IpcpType(IntEnum):
    """
    IPCP types available in Ouroboros.
    """

    LOCAL = lib.IPCP_LOCAL
    UNICAST = lib.IPCP_UNICAST
    BROADCAST = lib.IPCP_BROADCAST


class PoaType(IntEnum):
    """
    The medium a PoA sits on.
    """

    UDP4 = lib.POA_UDP4
    UDP6 = lib.POA_UDP6
    ETH = lib.POA_ETH


class AddressAuthPolicy(IntEnum):
    """
    Address authority policies for unicast IPCPs.
    """

    FLAT_RANDOM = lib.ADDR_AUTH_FLAT_RANDOM


class LinkStatePolicy(IntEnum):
    """
    Link state routing policies.
    """

    SIMPLE = lib.LS_SIMPLE
    LFA = lib.LS_LFA
    ECMP = lib.LS_ECMP


class RoutingPolicy(IntEnum):
    """
    Routing policies.
    """

    LINK_STATE = lib.ROUTING_LINK_STATE


class CongestionAvoidPolicy(IntEnum):
    """
    Congestion avoidance policies.
    """

    NONE = lib.CA_NONE
    MB_ECN = lib.CA_MB_ECN


class DirectoryPolicy(IntEnum):
    """
    Directory policies.
    """

    DHT = lib.DIR_DHT


class DirectoryHashAlgo(IntEnum):
    """
    Directory hash algorithms.
    """

    SHA3_224 = lib.DIR_HASH_SHA3_224
    SHA3_256 = lib.DIR_HASH_SHA3_256
    SHA3_384 = lib.DIR_HASH_SHA3_384
    SHA3_512 = lib.DIR_HASH_SHA3_512


class LoadBalancePolicy(IntEnum):
    """
    Load balancing policies for names.
    """

    ROUND_ROBIN = lib.LB_RR
    SPILL = lib.LB_SPILL


@dataclass
class LinkStateConfig:
    """
    Configuration for link state routing.
    """

    pol: LinkStatePolicy = LinkStatePolicy.SIMPLE
    t_recalc: int = 4
    t_update: int = 15
    t_timeo: int = 60


@dataclass
class RoutingConfig:
    """
    Routing configuration.
    """

    pol: RoutingPolicy = RoutingPolicy.LINK_STATE
    ls: LinkStateConfig = field(default_factory=LinkStateConfig)


@dataclass
class DtConfig:
    """
    Data transfer configuration for unicast IPCPs.
    """

    addr_size: int = 4
    eid_size: int = 8
    max_ttl: int = 60
    routing: RoutingConfig = field(default_factory=RoutingConfig)


@dataclass
class DhtConfig:
    """
    DHT directory configuration.
    """

    alpha: int = 3
    k: int = 8
    t_expire: int = 86400
    t_refresh: int = 900
    t_replicate: int = 900


@dataclass
class DirConfig:
    """
    Directory configuration.
    """

    pol: DirectoryPolicy = DirectoryPolicy.DHT
    dht: DhtConfig = field(default_factory=DhtConfig)


@dataclass
class UnicastConfig:
    """
    Configuration for unicast IPCPs.
    """

    dt: DtConfig = field(default_factory=DtConfig)
    dir: DirConfig = field(default_factory=DirConfig)
    addr_auth: AddressAuthPolicy = AddressAuthPolicy.FLAT_RANDOM
    cong_avoid: CongestionAvoidPolicy = CongestionAvoidPolicy.MB_ECN


@dataclass
class EthPoa:
    """
    Configuration for an Ethernet PoA.

    The PoA is named by its device *dev*. *mac* is reported by
    :func:`list_poas`; it is not settable when attaching.
    """

    dev: str = ""
    mac: str = ""
    ethertype: int = lib.POA_ETHERTYPE


@dataclass
class Udp4Poa:
    """
    Configuration for a UDP/IPv4 PoA.
    """

    ip_addr: str = "0.0.0.0"
    port: int = lib.POA_UDP_PORT


@dataclass
class Udp6Poa:
    """
    Configuration for a UDP/IPv6 PoA.
    """

    ip_addr: str = "::"
    port: int = lib.POA_UDP_PORT


@dataclass
class PoaSpec:
    """
    One PoA an IPCP attaches to.

    Exactly one of *udp4*, *udp6* or *eth* must be set.
    """

    udp4: Optional[Udp4Poa] = None
    udp6: Optional[Udp6Poa] = None
    eth: Optional[EthPoa] = None


@dataclass
class PoaAddr:
    """
    Address of a peer PoA.

    *poa_type* is an :class:`PoaType`. For UDP, *addr* is an IP
    literal or a host name the IRM resolves. For Ethernet the peer
    is resolved by name query and our own PoA may be pinned by
    *dev*.
    """

    poa_type: PoaType
    addr: str = ""
    port: int = lib.POA_UDP_PORT
    ethertype: int = lib.POA_ETHERTYPE
    dev: str = ""


@dataclass
class IpcpConfig:
    """
    Configuration for bootstrapping an IPCP.
    """

    ipcp_type: IpcpType
    layer_name: str = ""
    dir_hash_algo: DirectoryHashAlgo = DirectoryHashAlgo.SHA3_256
    unicast: Optional[UnicastConfig] = None


@dataclass
class NameSecPaths:
    """
    Security paths for a name.
    """

    sec: str = ""
    key: str = ""
    crt: str = ""


@dataclass
class NameInfo:
    """
    Information about a registered name.
    """

    name: str
    pol_lb: LoadBalancePolicy = LoadBalancePolicy.ROUND_ROBIN
    server_sec: NameSecPaths = field(default_factory=NameSecPaths)
    client_sec: NameSecPaths = field(default_factory=NameSecPaths)


@dataclass
class IpcpInfo:
    """
    Information about a running IPCP.
    """

    pid: int
    type: IpcpType
    name: str
    layer: str
    transit: bool = True


def _poa_spec_to_c(poa: PoaSpec) -> Any:
    """
    Convert an :class:`PoaSpec` to a C ``struct poa_spec *``.
    """

    media = [m for m in ("udp4", "udp6", "eth") if getattr(poa, m) is not None]
    if len(media) != 1:
        raise ValueError(
            "A PoA needs exactly one of udp4, udp6 or eth, got "
            f"{', '.join(media) if media else 'none'}."
        )

    _poa = ffi.new("struct poa_spec *")

    if poa.udp4 is not None:
        if lib.poa_spec_set_udp(_poa, 0, poa.udp4.ip_addr.encode(), poa.udp4.port) != 0:
            raise ValueError(f"Invalid IPv4 address: {poa.udp4.ip_addr}")

        return _poa

    if poa.udp6 is not None:
        if lib.poa_spec_set_udp(_poa, 1, poa.udp6.ip_addr.encode(), poa.udp6.port) != 0:
            raise ValueError(f"Invalid IPv6 address: {poa.udp6.ip_addr}")

        return _poa

    if poa.eth.dev == "":
        raise ValueError("An Ethernet PoA needs a device name (dev).")

    if lib.poa_spec_set_eth(_poa, poa.eth.dev.encode(), poa.eth.ethertype) != 0:
        raise ValueError(f"Invalid Ethernet PoA: dev={poa.eth.dev!r}")

    return _poa


def _poa_spec_from_c(_poa: Any) -> PoaSpec:
    """
    Convert a C ``struct poa_spec_py *`` to a :class:`PoaSpec`.
    """

    poa_type = PoaType(_poa.type)
    addr = ffi.string(_poa.addr).decode()

    if poa_type == PoaType.UDP4:
        return PoaSpec(udp4=Udp4Poa(ip_addr=addr, port=_poa.port))

    if poa_type == PoaType.UDP6:
        return PoaSpec(udp6=Udp6Poa(ip_addr=addr, port=_poa.port))

    return PoaSpec(
        eth=EthPoa(
            dev=ffi.string(_poa.dev).decode(),
            mac=ffi.string(_poa.mac).decode(),
            ethertype=_poa.ethertype,
        )
    )


def _poa_addr_to_c(addr: PoaAddr) -> Any:
    """
    Convert an :class:`PoaAddr` to a C ``struct poa_addr *``.

    A UDP address that is not an IP literal is passed on as a host name
    for the IRM to resolve.
    """

    _addr = ffi.new("struct poa_addr *")
    if (
        lib.poa_addr_set(
            _addr,
            int(addr.poa_type),
            addr.addr.encode(),
            addr.port,
            addr.ethertype,
            addr.dev.encode(),
        )
        != 0
    ):
        raise ValueError(f"Invalid PoA address: {addr}")

    return _addr


def _ipcp_config_to_c(conf: IpcpConfig) -> Any:
    """
    Convert an :class:`IpcpConfig` to a C ``struct ipcp_config *``.

    The layer name is truncated to the 255 bytes the C struct holds.
    """

    _conf = ffi.new("struct ipcp_config *")

    layer_name = conf.layer_name.encode()

    ffi.memmove(_conf.layer_info.name, layer_name, min(len(layer_name), 255))

    _conf.layer_info.dir_hash_algo = conf.dir_hash_algo

    _conf.type = conf.ipcp_type

    if conf.ipcp_type == IpcpType.UNICAST:
        uc = conf.unicast or UnicastConfig()
        _conf.unicast.dt.addr_size = uc.dt.addr_size
        _conf.unicast.dt.eid_size = uc.dt.eid_size
        _conf.unicast.dt.max_ttl = uc.dt.max_ttl
        _conf.unicast.dt.routing.pol = uc.dt.routing.pol
        _conf.unicast.dt.routing.ls.pol = uc.dt.routing.ls.pol
        _conf.unicast.dt.routing.ls.t_recalc = uc.dt.routing.ls.t_recalc
        _conf.unicast.dt.routing.ls.t_update = uc.dt.routing.ls.t_update
        _conf.unicast.dt.routing.ls.t_timeo = uc.dt.routing.ls.t_timeo
        _conf.unicast.dir.pol = uc.dir.pol
        _conf.unicast.dir.dht.params.alpha = uc.dir.dht.alpha
        _conf.unicast.dir.dht.params.k = uc.dir.dht.k
        _conf.unicast.dir.dht.params.t_expire = uc.dir.dht.t_expire
        _conf.unicast.dir.dht.params.t_refresh = uc.dir.dht.t_refresh
        _conf.unicast.dir.dht.params.t_replicate = uc.dir.dht.t_replicate
        _conf.unicast.addr_auth_type = uc.addr_auth
        _conf.unicast.cong_avoid = uc.cong_avoid

    return _conf


def _name_info_to_c(info: NameInfo) -> Any:
    """
    Convert a :class:`NameInfo` to a C ``struct name_info *``.
    """

    _info = ffi.new("struct name_info *")

    name = info.name.encode()

    ffi.memmove(_info.name, name, min(len(name), 255))

    _info.pol_lb = info.pol_lb

    for attr, sec in (("s", info.server_sec), ("c", info.client_sec)):
        sec_paths = getattr(_info, attr)

        for fld in ("sec", "key", "crt"):
            val = getattr(sec, fld).encode()

            ffi.memmove(getattr(sec_paths, fld), val, min(len(val), 511))

    return _info


def create_ipcp(name: str, ipcp_type: IpcpType, transit: bool = True) -> int:
    """
    Create a new IPCP.

    :param name:      Name for the IPCP.
    :param ipcp_type: Type of IPCP to create.
    :param transit:   Whether the IPCP forwards traffic for others.
    :return:          PID of the created IPCP.
    :raises IpcpCreateError: If creation fails or the IPCP is not found.
    """

    flags = lib.IPCP_FLAG_TRANSIT if transit else 0

    raise_errno(
        lib.irm_create_ipcp(name.encode(), ipcp_type, flags),
        default=IpcpCreateError,
    )

    for info in list_ipcps():
        if info.name == name:
            return info.pid

    raise IpcpCreateError(f"IPCP '{name}' created but not found in list")


def set_transit(pid: int, transit: bool) -> None:
    """
    Turn transit on or off on a running IPCP.

    :param pid:     PID of the IPCP.
    :param transit: Whether the IPCP forwards traffic for others.
    :raises IrmError: If the flag could not be set.
    """

    flags = lib.IPCP_FLAG_TRANSIT if transit else 0

    raise_errno(
        lib.irm_set_ipcp_flags(pid, flags, lib.IPCP_FLAG_TRANSIT),
        default=IrmError,
    )


def destroy_ipcp(pid: int) -> None:
    """
    Destroy an IPCP.

    :param pid: PID of the IPCP to destroy.
    :raises IrmError: If the IPCP could not be destroyed.
    """

    raise_errno(lib.irm_destroy_ipcp(pid), default=IrmError)


def list_ipcps() -> List[IpcpInfo]:
    """
    List all running IPCPs.

    :return: List of :class:`IpcpInfo` objects.
    :raises IrmError: If the IPCPs could not be listed.
    """

    _ipcps = ffi.new("struct ipcp_list_info **")
    n = raise_errno(lib.irm_list_ipcps(_ipcps), default=IrmError)

    result = []

    for i in range(n):
        info = _ipcps[0][i]

        result.append(
            IpcpInfo(
                pid=info.pid,
                type=IpcpType(info.type),
                name=ffi.string(info.name).decode(),
                layer=ffi.string(info.layer).decode(),
                transit=bool(info.flags & lib.IPCP_FLAG_TRANSIT),
            )
        )

    if n > 0:
        lib.free(_ipcps[0])

    return result


def enroll_ipcp(pid: int, dst: str, addr: Optional[PoaAddr] = None) -> None:
    """
    Enroll an IPCP in a layer.

    The IPCP must already be attached to a PoA that can reach
    *addr*; see :func:`attach_ipcp`.

    :param pid:  PID of the IPCP to enroll.
    :param dst:  Name of a member of the layer to enroll with.
    :param addr: Address of the PoA to enroll over. If
                 *None*, *dst* is resolved through the IRM.
    :raises IpcpEnrollError: If the IPCP could not enroll with *dst*.
    """

    _addr = ffi.NULL if addr is None else _poa_addr_to_c(addr)

    raise_errno(lib.irm_enroll_ipcp(pid, dst.encode(), _addr), default=IpcpEnrollError)


def attach_ipcp(pid: int, poa: PoaSpec) -> None:
    """
    Attach an IPCP to a medium. Repeat for more than one PoA.

    :param pid: PID of the IPCP to attach.
    :param poa: The PoA to attach to.
    :raises IpcpAttachError: If the PoA could not be attached.
    """

    raise_errno(lib.irm_attach_ipcp(pid, _poa_spec_to_c(poa)), default=IpcpAttachError)


def detach_ipcp(pid: int, poa: PoaSpec) -> None:
    """
    Release a PoA an IPCP is attached to.

    :param pid: PID of the IPCP to detach.
    :param poa: The PoA to release.
    :raises IpcpAttachError: If the PoA could not be released.
    """

    raise_errno(lib.irm_detach_ipcp(pid, _poa_spec_to_c(poa)), default=IpcpAttachError)


def list_poas(pid: int) -> List[PoaSpec]:
    """
    List the PoAs an IPCP is attached to.

    :param pid: PID of the IPCP to query.
    :return: List of :class:`PoaSpec` objects.
    :raises IpcpAttachError: If the PoAs could not be listed.
    """

    _poas = ffi.new("struct poa_spec **")
    n = raise_errno(lib.irm_list_poas(pid, _poas), default=IpcpAttachError)

    _poa = ffi.new("struct poa_spec_py *")

    result = []

    try:
        for i in range(n):
            if lib.poa_spec_get(_poas[0], i, _poa) != 0:
                raise IpcpAttachError(f"IPCP {pid} reported an unknown PoA.")

            result.append(_poa_spec_from_c(_poa))
    finally:
        if n > 0:
            lib.free(_poas[0])

    return result


def bootstrap_ipcp(pid: int, conf: IpcpConfig) -> None:
    """
    Bootstrap an IPCP.

    :param pid:  PID of the IPCP to bootstrap.
    :param conf: Configuration for the IPCP.
    :raises IpcpBootstrapError: If the IPCP could not be bootstrapped.
    """

    _conf = _ipcp_config_to_c(conf)

    raise_errno(lib.irm_bootstrap_ipcp(pid, _conf), default=IpcpBootstrapError)


def connect_ipcp(
    pid: int,
    component: str,
    dst: str,
    qos: Optional[QoSSpec] = None,
    addr: Optional[PoaAddr] = None,
) -> None:
    """
    Connect an IPCP component to a destination.

    :param pid:       PID of the IPCP.
    :param component: :data:`DT_COMP` or :data:`MGMT_COMP`.
    :param dst:       Destination name.
    :param qos:       QoS specification for the connection.
    :param addr:      Address of the PoA to connect over. If
                      *None*, *dst* is resolved through the IRM.
    :raises IpcpConnectError: If *component* could not be
                              connected to *dst*.
    """

    _qos = qos_to_qosspec(ffi, qos)
    if _qos == ffi.NULL:
        _qos = ffi.new("qosspec_t *")

    _addr = ffi.NULL if addr is None else _poa_addr_to_c(addr)

    raise_errno(
        lib.irm_connect_ipcp(pid, dst.encode(), component.encode(), _qos[0], _addr),
        default=IpcpConnectError,
    )


def disconnect_ipcp(pid: int, component: str, dst: str) -> None:
    """
    Disconnect an IPCP component from a destination.

    :param pid:       PID of the IPCP.
    :param component: :data:`DT_COMP` or :data:`MGMT_COMP`.
    :param dst:       Destination name.
    :raises IpcpConnectError: If *component* could not be
                              disconnected from *dst*.
    """

    raise_errno(
        lib.irm_disconnect_ipcp(pid, dst.encode(), component.encode()),
        default=IpcpConnectError,
    )


def bind_program(prog: str, name: str, opts: int = 0, argv: Optional[List[str]] = None) -> None:
    """
    Bind a program to a name.

    :param prog: Path to the program.
    :param name: Name to bind to.
    :param opts: Bind options (e.g. :data:`BIND_AUTO`).
    :param argv: Arguments passed when the IRM starts the program.
    :raises BindError: If *prog* could not be bound to *name*.
    """

    if argv:
        argc = len(argv)
        _args = []

        for a in argv:
            _args.append(ffi.new("char[]", a.encode()))

        _argv = ffi.new("char *[]", _args)
    else:
        argc = 0
        _argv = ffi.NULL

    raise_errno(
        lib.irm_bind_program(prog.encode(), name.encode(), opts, argc, _argv),
        default=BindError,
    )


def unbind_program(prog: str, name: str) -> None:
    """
    Unbind a program from a name.

    :param prog: Path to the program.
    :param name: Name to unbind from.
    :raises BindError: If *prog* could not be unbound from *name*.
    """

    raise_errno(lib.irm_unbind_program(prog.encode(), name.encode()), default=BindError)


def bind_process(pid: int, name: str) -> None:
    """
    Bind a running process to a name.

    :param pid:  PID of the process.
    :param name: Name to bind to.
    :raises BindError: If the process could not be bound to *name*.
    """

    raise_errno(lib.irm_bind_process(pid, name.encode()), default=BindError)


def unbind_process(pid: int, name: str) -> None:
    """
    Unbind a process from a name.

    :param pid:  PID of the process.
    :param name: Name to unbind from.
    :raises BindError: If the process could not be unbound from *name*.
    """

    raise_errno(lib.irm_unbind_process(pid, name.encode()), default=BindError)


def create_name(info: NameInfo) -> None:
    """
    Create a name in the IRM.

    :param info: :class:`NameInfo` describing the name to create.
    :raises NameExistsError: If the name already exists.
    """

    _info = _name_info_to_c(info)

    raise_errno(lib.irm_create_name(_info), default=NameExistsError)


def destroy_name(name: str) -> None:
    """
    Destroy a name in the IRM.

    :param name: The name to destroy.
    :raises NameNotFoundError: If the name is unknown.
    """

    raise_errno(lib.irm_destroy_name(name.encode()), default=NameNotFoundError)


def list_names() -> List[NameInfo]:
    """
    List all registered names.

    :return: List of :class:`NameInfo` objects.
    :raises IrmError: If the names could not be listed.
    """

    _names = ffi.new("struct name_info **")
    n = raise_errno(lib.irm_list_names(_names), default=IrmError)

    result = []

    for i in range(n):
        info = _names[0][i]

        result.append(
            NameInfo(
                name=ffi.string(info.name).decode(),
                pol_lb=LoadBalancePolicy(info.pol_lb),
                server_sec=NameSecPaths(
                    sec=ffi.string(info.s.sec).decode(),
                    key=ffi.string(info.s.key).decode(),
                    crt=ffi.string(info.s.crt).decode(),
                ),
                client_sec=NameSecPaths(
                    sec=ffi.string(info.c.sec).decode(),
                    key=ffi.string(info.c.key).decode(),
                    crt=ffi.string(info.c.crt).decode(),
                ),
            )
        )

    if n > 0:
        lib.free(_names[0])

    return result


def reg_name(name: str, pid: int) -> None:
    """
    Register an IPCP to a name.

    :param name: The name to register.
    :param pid:  PID of the IPCP to register.
    :raises NameNotFoundError: If the name is unknown.
    """

    raise_errno(lib.irm_reg_name(name.encode(), pid), default=NameNotFoundError)


def unreg_name(name: str, pid: int) -> None:
    """
    Unregister an IPCP from a name.

    :param name: The name to unregister.
    :param pid:  PID of the IPCP to unregister.
    :raises NameNotFoundError: If the name or the registration
                               is unknown.
    """

    raise_errno(lib.irm_unreg_name(name.encode(), pid), default=NameNotFoundError)
