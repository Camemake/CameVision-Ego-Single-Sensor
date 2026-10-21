#!/usr/bin/env python3
import socket
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_telnet import run

print("=== board ===")
print(
    run(
        r"""
ps | grep -E 'hw_rtsp|isp_publish|v4l2-ctl|rkaiq_3A' | grep -v grep
ls -l /dev/shm/isp.nv12
tail -c 200 /userdata/hw-rtsp.log
netstat -lnt 2>/dev/null | grep 8554 || ss -lnt 2>/dev/null | grep 8554 || echo no-netstat
""",
        wait=6,
    )
)

print("=== OPTIONS ===")
s = socket.create_connection(("192.168.1.23", 8554), 5)
req = (
    "OPTIONS rtsp://192.168.1.23:8554/live RTSP/1.0\r\n"
    "CSeq: 1\r\n"
    "User-Agent: cv-probe\r\n\r\n"
)
s.sendall(req.encode())
s.settimeout(4)
print(s.recv(2048).decode("utf-8", "replace"))
s.close()

print("=== DESCRIBE ===")
s = socket.create_connection(("192.168.1.23", 8554), 5)
req = (
    "DESCRIBE rtsp://192.168.1.23:8554/live RTSP/1.0\r\n"
    "CSeq: 2\r\n"
    "Accept: application/sdp\r\n\r\n"
)
s.sendall(req.encode())
s.settimeout(4)
print(s.recv(4096).decode("utf-8", "replace"))
s.close()

for name in ("ffprobe", "ffmpeg"):
    try:
        r = subprocess.run(
            [
                name,
                "-rtsp_transport",
                "tcp",
                "-i",
                "rtsp://192.168.1.23:8554/live",
                "-hide_banner",
            ]
            + (["-v", "error", "-show_streams", "-select_streams", "v:0"] if name == "ffprobe" else ["-t", "1", "-f", "null", "-"]),
            capture_output=True,
            text=True,
            timeout=12,
        )
        print("===", name, "rc", r.returncode, "===")
        print((r.stderr or "")[-800])
        print((r.stdout or "")[-400])
        break
    except FileNotFoundError:
        continue
    except Exception as e:
        print(name, e)
