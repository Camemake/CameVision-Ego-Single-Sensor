#!/usr/bin/env python3
"""Telnet to the live CameVision board (wlan0). Avoids PowerShell $(...) expansion."""
import socket
import sys
import time

HOST = "192.168.1.72"
PORT = 2323


def run(cmd: str, wait: float = 4.0) -> str:
    s = socket.create_connection((HOST, PORT), 8)
    s.settimeout(wait + 2)
    time.sleep(0.25)
    try:
        s.recv(8192)
    except Exception:
        pass
    s.send((cmd.rstrip() + "\necho __END_CV__\n").encode())
    time.sleep(wait)
    chunks = []
    s.settimeout(1.5)
    while True:
        try:
            b = s.recv(65536)
            if not b:
                break
            chunks.append(b)
            if b"__END_CV__" in b:
                try:
                    chunks.append(s.recv(65536))
                except Exception:
                    pass
                break
        except Exception:
            break
    s.close()
    return b"".join(chunks).decode("utf-8", "replace")


if __name__ == "__main__":
    wait = 4.0
    args = sys.argv[1:]
    if args and args[0] == "--wait":
        wait = float(args[1])
        args = args[2:]
    cmd = args[0] if args else sys.stdin.read()
    sys.stdout.write(run(cmd, wait))
