#
# SPDX-FileCopyrightText: 2016 - 2026 Dimitri Staessens
# SPDX-License-Identifier: BSD-3-Clause
#

"""
A simple echo client/server example using Ouroboros flows.
"""

# Standalone demo; duplicates oecho_set.py.
# pylint: disable=duplicate-code

from __future__ import annotations

import argparse

from ouroboros.dev import flow_accept, flow_alloc


def client() -> None:
    """
    Send a message and print the echo reply.
    """

    with flow_alloc("oecho") as f:
        f.writeline("Hello, PyOuroboros!")
        print(f.readline())


def server() -> None:
    """
    Accept flows and echo back received messages.
    """

    print("Starting the server.")

    while True:
        with flow_accept() as f:
            print("New flow.")

            line = f.readline()

            print(f"Message from client is {line}")
            f.writeline(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple echo client/server')

    parser.add_argument('-l', '--listen', help='run as a server',
                        action='store_true')

    args = parser.parse_args()
    if args.listen:
        server()
    else:
        client()
