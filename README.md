# pyOuroboros
> a Python API for the Ouroboros recursive network prototype

## Dependencies

pyOuroboros requires <a href="https://ouroboros.rocks">Ouroboros</a>
to be installed (matching `major.minor` version — see [Versioning](#versioning)).

## Installation

To build and install pyOuroboros:

```shell
pip install .
```

Or for an editable install during development:

```shell
pip install -e .
```

## Basic Usage

Applications import each part of the API from its submodule
explicitly — flows, events and the control plane are three distinct
concerns, and the import line says which one is in use:

```Python
from ouroboros.dev   import Flow, flow_alloc, flow_accept, flow_join
from ouroboros.event import FEventQueue, FEventType, FlowSet
from ouroboros.irm   import create_ipcp, bootstrap_ipcp, reg_name
# or, for IRM operations that mirror the `irm` CLI tool:
from ouroboros.cli   import autoboot, destroy_ipcp
```

The pure-Python `errors` and `qos` modules are also re-exported at
the top level for convenience (`from ouroboros import QoSSpec,
OuroborosError`), but `dev`, `event`, `irm` and `cli` are only
available through their submodule path — importing them eagerly
from the top-level package would load the libouroboros CFFI
extensions on every `import ouroboros`, which is the wrong default
for a binding layer.

Server side: accept a flow.

```Python
f = flow_accept()
```

returns a new allocated `Flow` object.

Client side: allocate a flow to a certain _name_.

```Python
f = flow_alloc("name")
```

Broadcast: join a broadcast layer.

```Python
f = flow_join("name")
```

Deallocate a flow:

```Python
f.dealloc()
```

`dealloc()` is idempotent. To avoid calling it explicitly, use a
`with` statement — and any `Flow` that is garbage-collected without
being deallocated will be cleaned up too:

```Python
with flow_alloc("dst") as f:
    f.writeline("line")
    print(f.readline())
```

`Flow()` constructs an empty wrapper; `Flow(fd)` wraps an existing
flow descriptor. `f.alloc("name")` populates an empty wrapper:

```Python
f = Flow()
f.alloc("name")
```

To read / write on a flow:

```Python
f.read(count)        # read up to `count` bytes, return bytes
f.readline()         # read and decode as UTF-8, return str
f.write(buf, count)  # write up to `count` bytes from buffer
f.writeline(ln)      # encode `ln` as UTF-8 and write, return bytes written
```

## Quality of Service (QoS)

`QoSSpec` describes the QoS requested for a flow. It is a **frozen**
dataclass; construct a new spec to vary fields, or use
`dataclasses.replace(qos, ...)` to derive one.

```Python
from ouroboros.qos import QoSSpec, QoSService

qos = QoSSpec(service=QoSService.MESSAGE, loss=0, timeout=60000)
f = flow_alloc("name", qos)
```

The `service` field selects the framing / reliability class and
enables FRCT for values > 0:

```Python
class QoSService(IntEnum):
    RAW      # No FRCT; best-effort raw messages
    MESSAGE  # FRCT, reliable ordered messages
    STREAM   # FRCT, reliable ordered byte stream
```

A handful of predefined QoS specs mirror the ones in
`ouroboros/qos.h` (`_safe` enables an integrity check by setting
`ber=0`; `rt` trades reliability for latency):

```Python
from ouroboros import (
    QOS_RAW, QOS_RAW_SAFE,   # Raw best-effort
    QOS_RT,  QOS_RT_SAFE,    # Real-time, low latency
    QOS_MSG,                 # Reliable ordered messages
    QOS_STREAM,              # Reliable ordered byte stream
)

f = flow_alloc("name", QOS_STREAM)
```

## Manipulating flows

A number of methods are available to inspect and tune a `Flow`:

```Python
f.set_snd_timeout(0.5) # set timeout for blocking write (seconds)
f.set_rcv_timeout(1.0) # set timeout for blocking read (seconds)
f.get_snd_timeout()    # get timeout for blocking write
f.get_rcv_timeout()    # get timeout for blocking read
f.get_qos()            # get the QoSSpec for this flow
f.get_rx_queue_len()   # bytes pending in the rx buffer
f.get_tx_queue_len()   # bytes pending in the tx buffer
f.get_mtu()            # per-packet MTU (0 if unknown)
f.set_flags(flags)     # replace the full set of flags
f.add_flags(flags)     # OR new flags into the current flow flags
f.remove_flags(flags)  # clear flags while preserving the rest
f.get_flags()          # get the flags for this flow
f.fileno()             # underlying ouroboros flow descriptor
```

The flags are specified as an `IntFlag` enum, `FlowProperties`:

```Python
class FlowProperties(IntFlag):
    READ_ONLY
    WRITE_ONLY
    READ_WRITE
    DOWN
    NON_BLOCKING_READ
    NON_BLOCKING_WRITE
    NON_BLOCKING            # NON_BLOCKING_READ | NON_BLOCKING_WRITE
    NO_PARTIAL_READ
    NO_PARTIAL_WRITE
```

For FRCT-enabled flows (`service > 0`), the FRCT state can be tuned:

```Python
from ouroboros.dev import FrctFlags

f.set_frct_flags(FrctFlags.RESCNTL | FrctFlags.LINGER)
f.get_frct_flags()
f.set_frct_max_sdu(size)        # max reassembly SDU (bytes)
f.get_frct_max_sdu()
f.set_frct_rcv_ring_size(size)  # stream rcv ring (bytes, pow2)
f.get_frct_rcv_ring_size()
f.set_frct_rto_min(rto_ns)      # RTO floor in nanoseconds
f.get_frct_rto_min()
```

FRCT flags: `FrctFlags.RETRANSMIT` (fixed at flow alloc),
`FrctFlags.RESCNTL`, `FrctFlags.LINGER`.

See the Ouroboros fccntl documentation for more details.

```shell
man fccntl
```

## Event API

Multiple flows can be monitored for activity in parallel using
`FlowSet` and `FEventQueue` objects.

A `FlowSet` groups `Flow` objects together. It can be constructed
with an optional list of flows; flows can be added or removed at any
time:

```Python
from ouroboros.event import FlowSet

fs = FlowSet()    # create an empty flow set
fs.add(f)         # add a Flow `f` to this set
fs.remove(f)      # remove a Flow `f` from this set
fs.zero()         # remove all Flows from this set
```

An `FEventQueue` stores pending events on flows. Event types:

```Python
class FEventType(IntFlag):
    FLOW_PKT
    FLOW_DOWN
    FLOW_UP
    FLOW_ALLOC
    FLOW_DEALLOC
    FLOW_PEER
```

`FlowSet.wait()` populates an `FEventQueue` from a set; pending
events are then drained via `FEventQueue.next()`:

```Python
from ouroboros.event import FEventQueue, FEventType, FlowSet

fq = FEventQueue()
fs = FlowSet([f1, f2, f3])
fs.wait(fq, timeo=1.0)        # block up to 1 second
while True:
    try:
        f, t = fq.next()
    except OuroborosError:
        break                 # queue drained
    if t == FEventType.FLOW_PKT:
        msg = f.readline()
    ...
fs.destroy()
```

Both `FlowSet` and `FEventQueue` are context managers (preferred):

```Python
with FEventQueue() as fq, FlowSet([f]) as fs:
    fs.wait(fq)
    f2, t = fq.next()
    if t == FEventType.FLOW_PKT:
        line = f2.readline()
```

`destroy()` is idempotent; GC will also reclaim the underlying C
handles when the wrapper goes out of scope.

## Error handling

All pyOuroboros exceptions derive from `OuroborosError`. The
hierarchy mirrors stdlib conventions: flow-plane and IRM-plane errors
have their own base classes, and several specific subclasses inherit
from Python builtins so they can be caught either way.

```
OuroborosError
├── IrmError
│   ├── IpcpCreateError, IpcpBootstrapError, IpcpEnrollError
│   ├── IpcpConnectError, IpcpTypeError (ValueError), IpcpStateError
│   ├── IrmdError, IpcpdError, BindError
│   └── NameNotFoundError, NameExistsError, InvalidNameError (ValueError)
└── FlowError
    ├── FlowAlreadyAllocatedError, FlowNotAllocatedError
    ├── FlowDownError (ConnectionError), FlowPeerError (FlowDownError)
    ├── FlowPermissionError (PermissionError)
    ├── FlowTimeout (TimeoutError)
    ├── FlowCryptError, FlowAuthError, FlowReplayError
    └── FlowEventError
FlowDeallocWarning (Warning)
```

ouroboros errno codes (`ENOTALLOC`, `EFLOWDOWN`, `EFLOWPEER`,
`ENAME`, `ECRYPT`, ...) translate to the matching semantic subclass;
ambiguous libc errnos (`ETIMEDOUT`, `EAGAIN`, `ENOTCONN`,
`ECONNRESET`) translate to the stdlib base class.

```Python
from ouroboros import OuroborosError, FlowDownError

try:
    f.read()
except TimeoutError:
    ...                  # rcv timeout elapsed
except FlowDownError:
    ...                  # peer went away
except OuroborosError as e:
    log.warning("flow error: %s", e)
```

## IRM API

The IRM (IPC Resource Manager) module exposes the raw C API for
managing IPCPs, names, and bindings:

```Python
from ouroboros.irm import (
    IpcpType, IpcpConfig, NameInfo, BIND_AUTO, DT_COMP, MGMT_COMP,
    create_ipcp, bootstrap_ipcp, enroll_ipcp, destroy_ipcp, list_ipcps,
    connect_ipcp, disconnect_ipcp,
    create_name, destroy_name, list_names, reg_name, unreg_name,
    bind_program, unbind_program, bind_process, unbind_process,
)
```

For most use cases, the higher-level [`ouroboros.cli`](#cli-helpers)
wrappers are easier to work with — they mirror the `irm` CLI tool and
are keyed by IPCP name.

### IPCP Management

Create, bootstrap, enroll, and destroy IPCPs:

```Python
# Create a local IPCP
pid = create_ipcp("my_ipcp", IpcpType.LOCAL)

# Bootstrap it into a layer
conf = IpcpConfig(ipcp_type=IpcpType.LOCAL, layer_name="my_layer")
bootstrap_ipcp(pid, conf)

# List all running IPCPs
for ipcp in list_ipcps():
    print(ipcp)

# Enroll an IPCP
enroll_ipcp(pid, "enrollment_dst")

# Destroy an IPCP
destroy_ipcp(pid)
```

IPCP types: `LOCAL`, `UNICAST`, `BROADCAST`, `ETH_LLC`, `ETH_DIX`,
`UDP4`, `UDP6`.

### IPCP Configuration

`IpcpConfig` is a dataclass used to bootstrap an IPCP. It takes
the following fields:

```Python
IpcpConfig(
    ipcp_type,                                   # IpcpType (required)
    layer_name="",                               # Layer name (string)
    dir_hash_algo=DirectoryHashAlgo.SHA3_256,    # Hash algorithm
    unicast=None, eth=None, udp4=None, udp6=None # Type-specific config
)
```

`dir_hash_algo` can be `SHA3_224`, `SHA3_256`, `SHA3_384`, or
`SHA3_512`.

#### Local and Broadcast IPCPs

Local and broadcast IPCPs need no type-specific configuration:

```Python
conf = IpcpConfig(ipcp_type=IpcpType.LOCAL, layer_name="local_layer")
conf = IpcpConfig(ipcp_type=IpcpType.BROADCAST, layer_name="bc_layer")
```

#### Unicast IPCPs

Unicast IPCPs have the most detailed configuration:

```Python
conf = IpcpConfig(
    ipcp_type=IpcpType.UNICAST,
    layer_name="my_layer",
    unicast=UnicastConfig(
        dt=DtConfig(
            addr_size=4,       # Address size in bytes (default: 4)
            eid_size=8,        # Endpoint ID size in bytes (default: 8)
            max_ttl=60,        # Maximum time-to-live (default: 60)
            routing=RoutingConfig(
                pol=RoutingPolicy.LINK_STATE,
                ls=LinkStateConfig(
                    pol=LinkStatePolicy.SIMPLE,  # SIMPLE, LFA, or ECMP
                    t_recalc=4,                  # Recalculation interval (s)
                    t_update=15,                 # Update interval (s)
                    t_timeo=60                   # Timeout (s)
                )
            )
        ),
        dir=DirConfig(
            pol=DirectoryPolicy.DHT,
            dht=DhtConfig(
                alpha=3,           # Concurrency parameter
                k=8,               # Replication factor
                t_expire=86400,    # Entry expiry time (s)
                t_refresh=900,     # Refresh interval (s)
                t_replicate=900    # Replication interval (s)
            )
        ),
        addr_auth=AddressAuthPolicy.FLAT_RANDOM,
        cong_avoid=CongestionAvoidPolicy.MB_ECN  # or NONE
    )
)
```

All sub-configs have sensible defaults, so for most cases a simpler
form suffices:

```Python
conf = IpcpConfig(
    ipcp_type=IpcpType.UNICAST,
    layer_name="my_layer",
    unicast=UnicastConfig()
)
```

#### Ethernet IPCPs (LLC and DIX)

```Python
conf = IpcpConfig(
    ipcp_type=IpcpType.ETH_LLC,  # or IpcpType.ETH_DIX
    layer_name="eth_layer",
    eth=EthConfig(
        dev="eth0",         # Network device name
        ethertype=0xA000    # Ethertype (mainly for DIX)
    )
)
```

#### UDP IPCPs

For UDP over IPv4:

```Python
conf = IpcpConfig(
    ipcp_type=IpcpType.UDP4,
    layer_name="udp4_layer",
    udp4=Udp4Config(
        ip_addr="192.168.1.1",    # Local IP address
        dns_addr="192.168.1.254", # DNS server address
        port=3435                 # UDP port (default: 3435)
    )
)
```

For UDP over IPv6:

```Python
conf = IpcpConfig(
    ipcp_type=IpcpType.UDP6,
    layer_name="udp6_layer",
    udp6=Udp6Config(
        ip_addr="fd00::1",       # Local IPv6 address
        dns_addr="fd00::fe",     # DNS server address
        port=3435                # UDP port (default: 3435)
    )
)
```

### Connecting IPCP Components

```Python
connect_ipcp(pid, DT_COMP, "destination")       # data transfer plane
connect_ipcp(pid, MGMT_COMP, "destination")     # management plane
disconnect_ipcp(pid, DT_COMP, "destination")
```

`connect_ipcp` optionally takes a `qos=QoSSpec(...)` argument.

### Name Management

Create, destroy, and list names:

```Python
# Create a name
info = NameInfo(name="my_name", pol_lb=LoadBalancePolicy.ROUND_ROBIN)
create_name(info)

# Register / unregister an IPCP to a name
reg_name("my_name", pid)
unreg_name("my_name", pid)

# List all registered names
for name in list_names():
    print(name.name)

# Destroy a name
destroy_name("my_name")
```

### Binding Programs and Processes

```Python
# Bind a program to a name (auto-start on flow allocation)
bind_program("/usr/bin/my_server", "my_name", BIND_AUTO)
unbind_program("/usr/bin/my_server", "my_name")

# Bind a running process to a name
bind_process(pid, "my_name")
unbind_process(pid, "my_name")
```

## CLI helpers

`ouroboros.cli` mirrors the C-side `ouroboros/tools/irm` command-line
tool. The functions take IPCP _names_ (not pids), call `realpath()`
on programs, and handle the `autobind` flag for bootstrap / enroll:

```Python
from ouroboros.cli import (
    create_ipcp, destroy_ipcp, bootstrap_ipcp, enroll_ipcp,
    connect_ipcp, disconnect_ipcp,
    bind_program, bind_ipcp, autoboot,
    reg_name, unreg_name,
    IpcpType, IpcpConfig,                    # re-exported for convenience
)

# Create + bootstrap + autobind in one step
autoboot("my_ipcp", IpcpType.LOCAL, layer="my_layer")

# Bootstrap with autobind (binds the IPCP to its name and layer first)
conf = IpcpConfig(ipcp_type=IpcpType.UNICAST, layer_name="dc")
bootstrap_ipcp("my_ipcp", conf, autobind=True)

# Register a name with multiple IPCPs at once
reg_name("server", ipcps=["ipcp1", "ipcp2"])
```

See the module docstring for the full CLI-command ↔ Python mapping.

## Examples

See the [`examples/`](examples/) directory for runnable client/server
demos.

## Versioning

pyOuroboros uses `setuptools_scm` to derive its version from git tags.

**Compatibility contract across Ouroboros repositories:**

| Scope | Rule |
|---|---|
| ouroboros (C) ↔ pyouroboros / rumba | Shared `major.minor`, C side at least equal |
| pyouroboros ↔ rumba ↔ ouroboros-integration | Lockstep `major.minor.patch`, released together |

## License

pyOuroboros is LGPLv2.1. The examples are 3-clause BSD.
