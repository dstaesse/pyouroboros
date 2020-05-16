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
qos = QoSSpec(loss=0, cypher_s=256)
f = flow_alloc("name", qos)
```

will create a new flow with FRCP retransmission enabled and encrypted
using a 256-bit ECDHE-AES-SHA3 cypher.

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

## Examples

Some example code is in the examples folder.

## License
pyOuorboros is LGPLv2.1. The examples are 3-clause BSD.
