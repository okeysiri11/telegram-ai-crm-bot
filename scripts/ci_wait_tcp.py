#!/usr/bin/env python3
"""Wait until TCP ports on 127.0.0.1 accept connections (GitHub Actions services)."""

from __future__ import annotations

import socket
import sys
import time


def _open(port: int) -> bool:
    sock = socket.socket()
    sock.settimeout(1)
    try:
        sock.connect(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def main() -> int:
    ports = [int(p) for p in sys.argv[1:]]
    if not ports:
        print("usage: ci_wait_tcp.py PORT [PORT ...]", file=sys.stderr)
        return 2
    deadline = time.time() + 60
    while time.time() < deadline:
        if all(_open(p) for p in ports):
            return 0
        time.sleep(2)
    print("timeout waiting for ports:", ports, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
