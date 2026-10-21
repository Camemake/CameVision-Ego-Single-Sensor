#!/usr/bin/env python3
import socket
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_telnet import run

HOST = "192.168.1.23"
OV = Path(
    r"C:\Users\stefa\Desktop\CameVision Single\restore\recovery-3-20260822-uvc-wifi-rkaiq\overlay"
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


def put(src: Path, dst: str) -> None:
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    telnet_send(
        "cat > %s << 'ENDFILE'\n%sENDFILE\nchmod 755 %s" % (dst, text, dst),
        wait=4,
    )
    print("wrote", dst)


put(OV / "isp_publish.py", "/userdata/isp_publish.py")
put(OV / "hw_rtsp.py", "/userdata/hw_rtsp.py")
print(
    run(
        r"""
export PATH=/oem/usr/bin:/usr/bin:/bin:$PATH
# stop producers
if [ -f /userdata/hw-rtsp.pid ]; then kill $(cat /userdata/hw-rtsp.pid) 2>/dev/null; fi
if [ -f /tmp/isp-pub.pid ]; then kill $(cat /tmp/isp-pub.pid) 2>/dev/null; fi
if [ -f /tmp/uvc-isp.pid ]; then kill $(cat /tmp/uvc-isp.pid) 2>/dev/null; fi
for p in $(ps | grep -E 'hw_rtsp|isp_publish|v4l2-ctl' | grep -v grep | awk '{print $1}'); do kill $p; done
sleep 1
rm -f /dev/shm/isp.nv12 /dev/shm/isp.tmp /tmp/hw_one.h264
mkfifo /tmp/cam.nv12 2>/dev/null
python3 -c 'import fcntl,os; fd=os.open("/tmp/cam.nv12", os.O_RDWR); fcntl.fcntl(fd,1031,8388608); os.close(fd)'
# publisher first so FIFO has a reader
start-stop-daemon -S -b -q -m -p /tmp/isp-pub.pid -x /usr/bin/python3 -- /userdata/isp_publish.py
sleep 0.3
setsid nohup sh -c 'while true; do v4l2-ctl -d /dev/video13 --stream-mmap=8 --stream-to=/tmp/cam.nv12 --stream-poll >>/userdata/v4l2-stream.log 2>&1; echo restart >>/userdata/v4l2-stream.log; sleep 0.3; done' </dev/null >/dev/null 2>&1 &
echo $! >/tmp/uvc-isp.pid
sleep 1
start-stop-daemon -S -b -q -m -p /userdata/hw-rtsp.pid -x /usr/bin/python3 -- /userdata/hw_rtsp.py
sleep 3
echo === ps ===
ps | grep -E 'hw_rtsp|isp_publish|v4l2-ctl|rkaiq_3A' | grep -v grep
echo === mtime ===
python3 - << 'PY'
import os,time
p="/dev/shm/isp.nv12"
seen=set()
for i in range(6):
    try:
        st=os.stat(p)
        m=getattr(st,"st_mtime_ns",0)
        seen.add(m)
        print(i, st.st_size, m)
    except Exception as e:
        print(i, e)
    time.sleep(0.35)
print("unique_mtimes", len(seen))
PY
""",
        wait=14,
    )
)
