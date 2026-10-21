#!/usr/bin/env python3
import socket
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_telnet import run

HOST = "192.168.1.23"
SRC = Path(
    r"C:\Users\stefa\Desktop\CameVision Single\restore\recovery-3-20260822-uvc-wifi-rkaiq\overlay\hw_rtsp.py"
)


def telnet_send(payload: str, wait: float) -> str:
    s = socket.create_connection((HOST, 2323), 8)
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


text = SRC.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if "ENDFILE" in text:
    raise SystemExit("sentinel")
print("push hw_rtsp.py", len(text))
print(
    telnet_send(
        "cat > /userdata/hw_rtsp.py << 'ENDFILE'\n%sENDFILE\nchmod 755 /userdata/hw_rtsp.py"
        % text,
        wait=4,
    )[-400:]
)
print(
    run(
        r"""
if [ -f /userdata/hw-rtsp.pid ]; then kill $(cat /userdata/hw-rtsp.pid) 2>/dev/null; fi
for p in $(ps | grep hw_rtsp | grep -v grep | awk '{print $1}'); do kill $p; done
sleep 1
start-stop-daemon -S -b -q -m -p /userdata/hw-rtsp.pid -x /usr/bin/python3 -- /userdata/hw_rtsp.py
sleep 1
ps | grep hw_rtsp | grep -v grep
grep Content-Base /userdata/hw_rtsp.py | head -2
""",
        wait=6,
    )
)
