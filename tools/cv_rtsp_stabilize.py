#!/usr/bin/env python3
"""Push the stable latest-frame RTSP stack and restart it."""
import socket
import sys
import time
from pathlib import Path

HOST = "192.168.1.23"
PORT = 2323
OV = Path(
    r"C:\Users\stefa\Desktop\CameVision Single\restore\recovery-3-20260822-uvc-wifi-rkaiq\overlay"
)


def telnet_send(payload: str, wait: float) -> str:
    s = socket.create_connection((HOST, PORT), 8)
    s.settimeout(wait + 3)
    time.sleep(0.25)
    try:
        s.recv(8192)
    except Exception:
        pass
    s.send((payload.rstrip() + "\necho __END_CV__\n").encode())
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


def put(src: Path, dst: str) -> None:
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if "ENDFILE" in text:
        raise SystemExit("sentinel in %s" % src)
    out = telnet_send(
        "cat > %s << 'ENDFILE'\n%sENDFILE\nchmod 755 %s" % (dst, text, dst),
        wait=5,
    )
    print("wrote", dst, len(text), "tail=", out[-120:].replace("\n", " "))


def main() -> int:
    print("=== probe ===")
    try:
        socket.create_connection((HOST, PORT), 5).close()
    except OSError as e:
        print("telnet down:", e)
        return 1
    put(OV / "hw_rtsp.py", "/userdata/hw_rtsp.py")
    put(OV / "isp_publish.py", "/userdata/isp_publish.py")
    put(OV / "camevision-wifi-rtsp.sh", "/userdata/camevision-wifi-rtsp.sh")
    print("=== restart ===")
    print(
        telnet_send(
            "setsid /userdata/camevision-wifi-rtsp.sh </dev/null >/userdata/wifi-rtsp.log 2>&1; sleep 8; echo === log ===; cat /userdata/wifi-rtsp.log; echo === enc ===; tail -c 300 /userdata/hw-rtsp.log 2>/dev/null; echo === v4l ===; tail -c 200 /userdata/v4l2-stream.log 2>/dev/null",
            wait=16,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
