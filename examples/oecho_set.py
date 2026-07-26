#
# SPDX-FileCopyrightText: 2016 - 2026 Dimitri Staessens
# SPDX-License-Identifier: BSD-3-Clause
#

"""
A simple echo client/server example using Ouroboros flow event sets.
"""

# Standalone demo; duplicates oecho.py.
# pylint: disable=duplicate-code

from __future__ import annotations

import argparse

from ouroboros.dev import flow_accept, flow_alloc
from ouroboros.event import FEventQueue, FEventType, FlowSet


def client() -> None:
    """
    Send a message and print the echo reply.
    """

    with flow_alloc("oecho") as f:
        f.writeline("Hello, PyOuroboros!")
        print(f.readline())


def server() -> None:
    """
    Accept flows and echo back received messages using flow events.
    """

    print("Starting the server.")

    while True:
        with flow_accept() as f:
            print("New flow.")
            with FEventQueue() as fq, FlowSet([f]) as fs:
                fs.wait(fq)

                f2, t = fq.next()

            if t != FEventType.FLOW_PKT:
                continue

            line = f2.readline()

            print(f"Message from client is {line}")
            f2.writeline(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple echo client/server')

    parser.add_argument('-l', '--listen', help='run as a server',
                        action='store_true')

    args = parser.parse_args()
    if args.listen:
        server()
    else:
        client()
