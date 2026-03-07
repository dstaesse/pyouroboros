#
# Ouroboros - Copyright (C) 2016 - 2026
#
# Python API for Ouroboros - IRM
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

from enum import IntEnum
from typing import List, Optional

from _ouroboros_irm_cffi import ffi, lib
from ouroboros.qos import QoSSpec


def _check_ouroboros_version():
    ouro_major = lib.OUROBOROS_VERSION_MAJOR
    ouro_minor = lib.OUROBOROS_VERSION_MINOR
    try:
        from importlib.metadata import version, PackageNotFoundError
        try:
            pyouro_parts = version('PyOuroboros').split('.')
        except PackageNotFoundError:
            return  # running from source, skip check
        if ouro_major != int(pyouro_parts[0]) or \
                ouro_minor != int(pyouro_parts[1]):
            raise RuntimeError(
                f"Ouroboros version mismatch: library is "
                f"{ouro_major}.{ouro_minor}, "
                f"pyouroboros is "
                f"{pyouro_parts[0]}.{pyouro_parts[1]}"
            )
    except ImportError:
        pass  # Python < 3.8


_check_ouroboros_version()


# Intentionally duplicated: irm uses a separate FFI (ouroboros-irm).
def _qos_to_qosspec(qos: QoSSpec):
    if qos is None:
        return ffi.NULL
    else:
        return ffi.new("qosspec_t *",
                       [qos.delay,
                        qos.bandwidth,
                        qos.availability,
                        qos.loss,
                        qos.ber,
                        qos.in_order,
                        qos.max_gap,
                        qos.timeout])

# --- Enumerations ---

class IpcpType(IntEnum):
    """IPCP types available in Ouroboros."""
    LOCAL     = lib.IPCP_LOCAL
    UNICAST   = lib.IPCP_UNICAST
    BROADCAST = lib.IPCP_BROADCAST
    ETH_LLC   = lib.IPCP_ETH_LLC
    ETH_DIX   = lib.IPCP_ETH_DIX
    UDP4      = lib.IPCP_UDP4
    UDP6      = lib.IPCP_UDP6


class AddressAuthPolicy(IntEnum):
    """Address authority policies for unicast IPCPs."""
    FLAT_RANDOM = lib.ADDR_AUTH_FLAT_RANDOM


class LinkStatePolicy(IntEnum):
    """Link state routing policies."""
    SIMPLE = lib.LS_SIMPLE
    LFA    = lib.LS_LFA
    ECMP   = lib.LS_ECMP


class RoutingPolicy(IntEnum):
    """Routing policies."""
    LINK_STATE = lib.ROUTING_LINK_STATE


class CongestionAvoidPolicy(IntEnum):
    """Congestion avoidance policies."""
    NONE   = lib.CA_NONE
    MB_ECN = lib.CA_MB_ECN


class DirectoryPolicy(IntEnum):
    """Directory policies."""
    DHT = lib.DIR_DHT


class DirectoryHashAlgo(IntEnum):
    """Directory hash algorithms."""
    SHA3_224 = lib.DIR_HASH_SHA3_224
    SHA3_256 = lib.DIR_HASH_SHA3_256
    SHA3_384 = lib.DIR_HASH_SHA3_384
    SHA3_512 = lib.DIR_HASH_SHA3_512


class LoadBalancePolicy(IntEnum):
    """Load balancing policies for names."""
    ROUND_ROBIN = lib.LB_RR
    SPILL       = lib.LB_SPILL


BIND_AUTO = lib.BIND_AUTO

# Unicast IPCP component names
DT_COMP   = "Data Transfer"
MGMT_COMP = "Management"


# --- Exceptions ---

class IrmError(Exception):
    """General IRM error."""
    pass


class IpcpCreateError(IrmError):
    pass


class IpcpBootstrapError(IrmError):
    pass


class IpcpEnrollError(IrmError):
    pass


class IpcpConnectError(IrmError):
    pass


class NameError(IrmError):
    pass


class BindError(IrmError):
    pass


# --- Configuration classes ---

class LinkStateConfig:
    """Configuration for link state routing."""

    def __init__(self,
                 pol: LinkStatePolicy = LinkStatePolicy.SIMPLE,
                 t_recalc: int = 4,
                 t_update: int = 15,
                 t_timeo: int = 60):
        self.pol = pol
        self.t_recalc = t_recalc
        self.t_update = t_update
        self.t_timeo = t_timeo


class RoutingConfig:
    """Routing configuration."""

    def __init__(self,
                 pol: RoutingPolicy = RoutingPolicy.LINK_STATE,
                 ls: LinkStateConfig = None):
        self.pol = pol
        self.ls = ls or LinkStateConfig()


class DtConfig:
    """Data transfer configuration for unicast IPCPs."""

    def __init__(self,
                 addr_size: int = 4,
                 eid_size: int = 8,
                 max_ttl: int = 60,
                 routing: RoutingConfig = None):
        self.addr_size = addr_size
        self.eid_size = eid_size
        self.max_ttl = max_ttl
        self.routing = routing or RoutingConfig()


class DhtConfig:
    """DHT directory configuration."""

    def __init__(self,
                 alpha: int = 3,
                 k: int = 8,
                 t_expire: int = 86400,
                 t_refresh: int = 900,
                 t_replicate: int = 900):
        self.alpha = alpha
        self.k = k
        self.t_expire = t_expire
        self.t_refresh = t_refresh
        self.t_replicate = t_replicate


class DirConfig:
    """Directory configuration."""

    def __init__(self,
                 pol: DirectoryPolicy = DirectoryPolicy.DHT,
                 dht: DhtConfig = None):
        self.pol = pol
        self.dht = dht or DhtConfig()


class UnicastConfig:
    """Configuration for unicast IPCPs."""

    def __init__(self,
                 dt: DtConfig = None,
                 dir: DirConfig = None,
                 addr_auth: AddressAuthPolicy = AddressAuthPolicy.FLAT_RANDOM,
                 cong_avoid: CongestionAvoidPolicy = CongestionAvoidPolicy.MB_ECN):
        self.dt = dt or DtConfig()
        self.dir = dir or DirConfig()
        self.addr_auth = addr_auth
        self.cong_avoid = cong_avoid


class EthConfig:
    """Configuration for Ethernet IPCPs (LLC or DIX)."""

    def __init__(self,
                 dev: str = "",
                 ethertype: int = 0xA000):
        self.dev = dev
        self.ethertype = ethertype


class Udp4Config:
    """Configuration for UDP over IPv4 IPCPs."""

    def __init__(self,
                 ip_addr: str = "0.0.0.0",
                 dns_addr: str = "0.0.0.0",
                 port: int = 3435):
        self.ip_addr = ip_addr
        self.dns_addr = dns_addr
        self.port = port


class Udp6Config:
    """Configuration for UDP over IPv6 IPCPs."""

    def __init__(self,
                 ip_addr: str = "::",
                 dns_addr: str = "::",
                 port: int = 3435):
        self.ip_addr = ip_addr
        self.dns_addr = dns_addr
        self.port = port


class IpcpConfig:
    """
    Configuration for bootstrapping an IPCP.

    Depending on the IPCP type, set the appropriate sub-configuration:
      - UNICAST:   unicast (UnicastConfig)
      - ETH_LLC:   eth (EthConfig)
      - ETH_DIX:   eth (EthConfig)
      - UDP4:      udp4 (Udp4Config)
      - UDP6:      udp6 (Udp6Config)
      - LOCAL:     no extra config needed
      - BROADCAST: no extra config needed
    """

    def __init__(self,
                 ipcp_type: IpcpType,
                 layer_name: str = "",
                 dir_hash_algo: DirectoryHashAlgo = DirectoryHashAlgo.SHA3_256,
                 unicast: UnicastConfig = None,
                 eth: EthConfig = None,
                 udp4: Udp4Config = None,
                 udp6: Udp6Config = None):
        self.ipcp_type = ipcp_type
        self.layer_name = layer_name
        self.dir_hash_algo = dir_hash_algo
        self.unicast = unicast
        self.eth = eth
        self.udp4 = udp4
        self.udp6 = udp6


class NameSecPaths:
    """Security paths for a name (encryption, key, certificate)."""

    def __init__(self,
                 enc: str = "",
                 key: str = "",
                 crt: str = ""):
        self.enc = enc
        self.key = key
        self.crt = crt


class NameInfo:
    """Information about a registered name."""

    def __init__(self,
                 name: str,
                 pol_lb: LoadBalancePolicy = LoadBalancePolicy.ROUND_ROBIN,
                 server_sec: NameSecPaths = None,
                 client_sec: NameSecPaths = None):
        self.name = name
        self.pol_lb = pol_lb
        self.server_sec = server_sec or NameSecPaths()
        self.client_sec = client_sec or NameSecPaths()


class IpcpInfo:
    """Information about a running IPCP (from list_ipcps)."""

    def __init__(self,
                 pid: int,
                 ipcp_type: IpcpType,
                 name: str,
                 layer: str):
        self.pid = pid
        self.type = ipcp_type
        self.name = name
        self.layer = layer

    def __repr__(self):
        return (f"IpcpInfo(pid={self.pid}, type={self.type.name}, "
                f"name='{self.name}', layer='{self.layer}')")


# --- Internal conversion functions ---

def _ipcp_config_to_c(conf: IpcpConfig):
    """Convert an IpcpConfig to a C struct ipcp_config *."""
    _conf = ffi.new("struct ipcp_config *")

    # Layer info
    layer_name = conf.layer_name.encode()
    ffi.memmove(_conf.layer_info.name, layer_name,
                min(len(layer_name), 255))
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

    elif conf.ipcp_type == IpcpType.ETH_LLC or conf.ipcp_type == IpcpType.ETH_DIX:
        ec = conf.eth or EthConfig()
        dev = ec.dev.encode()
        ffi.memmove(_conf.eth.dev, dev, min(len(dev), 255))
        _conf.eth.ethertype = ec.ethertype

    elif conf.ipcp_type == IpcpType.UDP4:
        uc = conf.udp4 or Udp4Config()
        _conf.udp4.port = uc.port
        if lib.ipcp_config_udp4_set_ip(_conf, uc.ip_addr.encode()) != 0:
            raise ValueError(f"Invalid IPv4 address: {uc.ip_addr}")
        if lib.ipcp_config_udp4_set_dns(_conf, uc.dns_addr.encode()) != 0:
            raise ValueError(f"Invalid IPv4 DNS address: {uc.dns_addr}")

    elif conf.ipcp_type == IpcpType.UDP6:
        uc = conf.udp6 or Udp6Config()
        _conf.udp6.port = uc.port
        if lib.ipcp_config_udp6_set_ip(_conf, uc.ip_addr.encode()) != 0:
            raise ValueError(f"Invalid IPv6 address: {uc.ip_addr}")
        if lib.ipcp_config_udp6_set_dns(_conf, uc.dns_addr.encode()) != 0:
            raise ValueError(f"Invalid IPv6 DNS address: {uc.dns_addr}")

    return _conf


def _name_info_to_c(info: NameInfo):
    """Convert a NameInfo to a C struct name_info *."""
    _info = ffi.new("struct name_info *")

    name = info.name.encode()
    ffi.memmove(_info.name, name, min(len(name), 255))
    _info.pol_lb = info.pol_lb

    for attr, sec in [('s', info.server_sec), ('c', info.client_sec)]:
        sec_paths = getattr(_info, attr)
        for field in ('enc', 'key', 'crt'):
            val = getattr(sec, field).encode()
            ffi.memmove(getattr(sec_paths, field), val,
                        min(len(val), 511))

    return _info


# --- IRM API functions ---

def create_ipcp(name: str,
                ipcp_type: IpcpType) -> int:
    """
    Create a new IPCP.

    :param name:      Name for the IPCP
    :param ipcp_type: Type of IPCP to create
    :return:          PID of the created IPCP
    """
    ret = lib.irm_create_ipcp(name.encode(), ipcp_type)
    if ret < 0:
        raise IpcpCreateError(f"Failed to create IPCP '{name}' "
                              f"of type {ipcp_type.name}")

    # The C function returns 0 on success, not the pid.
    # Look up the actual pid by name.
    for info in list_ipcps():
        if info.name == name:
            return info.pid

    raise IpcpCreateError(f"IPCP '{name}' created but not found in list")


def destroy_ipcp(pid: int) -> None:
    """
    Destroy an IPCP.

    :param pid: PID of the IPCP to destroy
    """
    if lib.irm_destroy_ipcp(pid) != 0:
        raise IrmError(f"Failed to destroy IPCP with pid {pid}")


def list_ipcps() -> List[IpcpInfo]:
    """
    List all running IPCPs.

    :return: List of IpcpInfo objects
    """
    _ipcps = ffi.new("struct ipcp_list_info **")
    n = lib.irm_list_ipcps(_ipcps)
    if n < 0:
        raise IrmError("Failed to list IPCPs")

    result = []
    for i in range(n):
        info = _ipcps[0][i]
        result.append(IpcpInfo(
            pid=info.pid,
            ipcp_type=IpcpType(info.type),
            name=ffi.string(info.name).decode(),
            layer=ffi.string(info.layer).decode()
        ))

    if n > 0:
        lib.free(_ipcps[0])

    return result


def enroll_ipcp(pid: int, dst: str) -> None:
    """
    Enroll an IPCP in a layer.

    :param pid: PID of the IPCP to enroll
    :param dst: Name to use for enrollment
    """
    if lib.irm_enroll_ipcp(pid, dst.encode()) != 0:
        raise IpcpEnrollError(f"Failed to enroll IPCP {pid} to '{dst}'")


def bootstrap_ipcp(pid: int, conf: IpcpConfig) -> None:
    """
    Bootstrap an IPCP.

    :param pid:  PID of the IPCP to bootstrap
    :param conf: Configuration for the IPCP
    """
    _conf = _ipcp_config_to_c(conf)
    if lib.irm_bootstrap_ipcp(pid, _conf) != 0:
        raise IpcpBootstrapError(f"Failed to bootstrap IPCP {pid}")


def connect_ipcp(pid: int,
                 component: str,
                 dst: str,
                 qos: QoSSpec = None) -> None:
    """
    Connect an IPCP component to a destination.

    :param pid:       PID of the IPCP
    :param component: Component to connect (DT_COMP or MGMT_COMP)
    :param dst:       Destination name
    :param qos:       QoS specification for the connection
    """
    _qos = _qos_to_qosspec(qos)
    if _qos == ffi.NULL:
        _qos = ffi.new("qosspec_t *")
    if lib.irm_connect_ipcp(pid, dst.encode(), component.encode(),
                            _qos[0]) != 0:
        raise IpcpConnectError(f"Failed to connect IPCP {pid} "
                               f"component '{component}' to '{dst}'")


def disconnect_ipcp(pid: int,
                    component: str,
                    dst: str) -> None:
    """
    Disconnect an IPCP component from a destination.

    :param pid:       PID of the IPCP
    :param component: Component to disconnect
    :param dst:       Destination name
    """
    if lib.irm_disconnect_ipcp(pid, dst.encode(),
                               component.encode()) != 0:
        raise IpcpConnectError(f"Failed to disconnect IPCP {pid} "
                               f"component '{component}' from '{dst}'")


def bind_program(prog: str,
                 name: str,
                 opts: int = 0,
                 argv: List[str] = None) -> None:
    """
    Bind a program to a name.

    :param prog: Path to the program
    :param name: Name to bind to
    :param opts: Bind options (e.g. BIND_AUTO)
    :param argv: Arguments to pass when the program is started
    """
    if argv:
        argc = len(argv)
        _argv = ffi.new("char *[]", [ffi.new("char[]", a.encode())
                                     for a in argv])
    else:
        argc = 0
        _argv = ffi.NULL

    if lib.irm_bind_program(prog.encode(), name.encode(),
                            opts, argc, _argv) != 0:
        raise BindError(f"Failed to bind program '{prog}' to name '{name}'")


def unbind_program(prog: str, name: str) -> None:
    """
    Unbind a program from a name.

    :param prog: Path to the program
    :param name: Name to unbind from
    """
    if lib.irm_unbind_program(prog.encode(), name.encode()) != 0:
        raise BindError(f"Failed to unbind program '{prog}' "
                        f"from name '{name}'")


def bind_process(pid: int, name: str) -> None:
    """
    Bind a running process to a name.

    :param pid:  PID of the process
    :param name: Name to bind to
    """
    if lib.irm_bind_process(pid, name.encode()) != 0:
        raise BindError(f"Failed to bind process {pid} to name '{name}'")


def unbind_process(pid: int, name: str) -> None:
    """
    Unbind a process from a name.

    :param pid:  PID of the process
    :param name: Name to unbind from
    """
    if lib.irm_unbind_process(pid, name.encode()) != 0:
        raise BindError(f"Failed to unbind process {pid} "
                        f"from name '{name}'")


def create_name(info: NameInfo) -> None:
    """
    Create a name in the IRM.

    :param info: NameInfo describing the name to create
    """
    _info = _name_info_to_c(info)
    if lib.irm_create_name(_info) != 0:
        raise NameError(f"Failed to create name '{info.name}'")


def destroy_name(name: str) -> None:
    """
    Destroy a name in the IRM.

    :param name: The name to destroy
    """
    if lib.irm_destroy_name(name.encode()) != 0:
        raise NameError(f"Failed to destroy name '{name}'")


def list_names() -> List[NameInfo]:
    """
    List all registered names.

    :return: List of NameInfo objects
    """
    _names = ffi.new("struct name_info **")
    n = lib.irm_list_names(_names)
    if n < 0:
        raise IrmError("Failed to list names")

    result = []
    for i in range(n):
        info = _names[0][i]
        ni = NameInfo(
            name=ffi.string(info.name).decode(),
            pol_lb=LoadBalancePolicy(info.pol_lb)
        )
        ni.server_sec = NameSecPaths(
            enc=ffi.string(info.s.enc).decode(),
            key=ffi.string(info.s.key).decode(),
            crt=ffi.string(info.s.crt).decode()
        )
        ni.client_sec = NameSecPaths(
            enc=ffi.string(info.c.enc).decode(),
            key=ffi.string(info.c.key).decode(),
            crt=ffi.string(info.c.crt).decode()
        )
        result.append(ni)

    if n > 0:
        lib.free(_names[0])

    return result


def reg_name(name: str, pid: int) -> None:
    """
    Register an IPCP to a name.

    :param name: The name to register
    :param pid:  PID of the IPCP to register
    """
    if lib.irm_reg_name(name.encode(), pid) != 0:
        raise NameError(f"Failed to register name '{name}' "
                        f"with IPCP {pid}")


def unreg_name(name: str, pid: int) -> None:
    """
    Unregister an IPCP from a name.

    :param name: The name to unregister
    :param pid:  PID of the IPCP to unregister
    """
    if lib.irm_unreg_name(name.encode(), pid) != 0:
        raise NameError(f"Failed to unregister name '{name}' "
                        f"from IPCP {pid}")
