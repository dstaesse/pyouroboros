# pyOuroboros
> a Python API for the Ouroboros recursive network prototype

## Dependencies

pyOuroboros requires <a href="https://ouroboros.rocks">Ouroboros</a>
to be installed

## Installation
To build and install PyOuroboros:

```shell
./setup.py install
```

## Basic Usage

```Python
from ouroboros.dev import *
```

Server side: Accepting a flow:

```Python
f = flow_accept()
```

returns a new allocated flow object.

Client side: Allocating a flow to a certain _name_:

```Python
f = flow_alloc("name")
```

returns a new allocated Flow object.

Broadcast:

```Python
f = flow_join("name")
```

returns a new allocated Flow object.

Deallocation:

```Python
f.dealloc()
```
To avoid having to call dealloc(), you can use the with statement:

```Python
with flow_alloc("dst") as f:
    f.writeline("line")
    print(f.readline())
```

deallocates the flow. After this call, the Flow object is not readable
or writeable anymore.

```Python
f.alloc("name")
```

 will allocate a new flow for an existing Flow object.

To read / write from a flow:

```Python
f.read(count)             # read up to _count_ bytes and return bytes
f.readline(count)         # read up to _count_ characters as a string
f.write(buf, count)       # write up to _count_ bytes from buffer
f.writeline(str, count)   # write up to _count_ characters from string
```

## Quality of Service (QoS)

The QoS spec details have not been finalized in Ouroboros. It is just
here to give a general idea and to control some basics of the flow.
You can specify a QoSSpec for flow allocation.

For instance,

```Python
qos = QoSSpec(loss=0, timeout=60000)
f = flow_alloc("name", qos)
```

will create a new flow with FRCP retransmission enabled that will
timeout if the peer is not responsive for 1 minute.

## Manipulating flows

A number of methods are available for how to interact with Flow

```Python
f.set_snd_timeout(0.5) # set timeout for blocking write
f.set_rcv_timeout(1.0) # set timeout for blocking read
f.get_snd_timeout()    # get timeout for blocking write
f.get_rcv_timeout()    # get timeout for blocking read
f.get_qos()            # get the QoSSpec for this flow
f.get_rx_queue_len()   # get the number of packets in the rx buffer
f.get_tx_queue_len()   # get the number of packets in the tx buffer
f.set_flags(flags)     # set a number of flags for this flow
f.get_flags()          # get the flags for this flow
```

The flags are specified as an enum FlowProperties:

```Python
class FlowProperties(IntFlag):
    ReadOnly
    WriteOnly
    ReadWrite
    Down
    NonBlockingRead
    NonBlockingWrite
    NonBlocking
    NoPartialRead
    NoPartialWrite
```

See the Ouroboros fccntl documentation for more details.

```shell
man fccntl
```

## Event API

Multiple flows can be monitored for activity in parallel using a
FlowSet and FEventQueue objects.

FlowSets allow grouping a bunch of Flow objects together to listen for
activity. It can be constructed with an optional list of Flows, or
flows can be added or removed using the following methods:

```Python
set = FlowSet() # create a flow set,
set.add(f)      # add a Flow 'f' to this set
set.remove(f)   # remove a Flow 'f' from this set
set.zero()      # remove all Flows in this set
```

An FEventQueue stores pending events on flows.

The event types are defined as follows:
```Python
class FEventType(IntFlag):
    FlowPkt
    FlowDown
    FlowUp
    FlowAlloc
    FlowDealloc
    FlowPeer
```

and can be obtained by calling the next method:

```Python
    f, t = fq.next() # Return active flow 'f' and type of event 't'
```

An FEventQueue is populated from a FlowSet.

```Python
fq = FEventQueue()            # Create an eventqueue
set = FlowSet([f1, f2, f3])   # Create a new set with a couple of Flow objects
set.wait(fq, timeo=1.0)       # Wait for 1 second or until event
while f, t = fq.next():
    if t == FEventType.FlowPkt:
        msg = f.readline()
    ...
set.destroy()
```

A flow_set must be destroyed when it goes out of scope.
To avoid having to call destroy, Python's with statement can be used:

```Python
fq = FEventQueue()
with FlowSet([f]) as fs:
    fs.wait(fq)
f2, t = fq.next()
if t == FEventType.FlowPkt:
    line = f2.readline()
```

## IRM API

The IRM (IPC Resource Manager) module allows managing IPCPs, names,
and bindings programmatically.

```Python
from ouroboros.irm import *
```

### IPCP Management

Creating, bootstrapping, enrolling, and destroying IPCPs:

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

The `IpcpConfig` class is used to bootstrap an IPCP. It takes
the following parameters:

```Python
IpcpConfig(
    ipcp_type,                                       # IpcpType (required)
    layer_name="",                                   # Layer name (string)
    dir_hash_algo=DirectoryHashAlgo.SHA3_256,        # Hash algorithm
    unicast=None, eth=None, udp4=None, udp6=None     # Type-specific config
)
```

The `dir_hash_algo` can be set to `SHA3_224`, `SHA3_256`, `SHA3_384`,
or `SHA3_512`.

#### Local and Broadcast IPCPs

Local and Broadcast IPCPs need no type-specific configuration:

```Python
conf = IpcpConfig(ipcp_type=IpcpType.LOCAL, layer_name="local_layer")
conf = IpcpConfig(ipcp_type=IpcpType.BROADCAST, layer_name="bc_layer")
```

#### Unicast IPCPs

Unicast IPCPs have the most detailed configuration, structured as
follows:

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
        cong_avoid=CongestionAvoidPolicy.MB_ECN  # or CA_NONE
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

Connecting and disconnecting IPCP components:

```Python
connect_ipcp(pid, DT_COMP, "destination")
disconnect_ipcp(pid, DT_COMP, "destination")
```

### Name Management

Creating, destroying, and listing names:

```Python
# Create a name
info = NameInfo(name="my_name", pol_lb=LoadBalancePolicy.ROUND_ROBIN)
create_name(info)

# Register/unregister an IPCP to a name
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

## Examples

Some example code is in the examples folder.

## License
pyOuroboros is LGPLv2.1. The examples are 3-clause BSD.
