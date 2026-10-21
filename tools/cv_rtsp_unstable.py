#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_telnet import run
print(run(r"""
echo === ps ===
ps | grep -E 'hw_rtsp|isp_publish|v4l2-ctl|rkaiq|mpi_enc' | grep -v grep
echo === logs ===
tail -c 400 /userdata/v4l2-stream.log
echo ---
echo === mtime/load ===
python3 - << 'PY'
import os, time
p="/dev/shm/isp.nv12"
seen=[]
for i in range(8):
    try:
        st=os.stat(p)
        seen.append(getattr(st,"st_mtime_ns",0))
        print(i, st.st_size, seen[-1])
    except Exception as e:
        print(i, e)
    time.sleep(0.25)
print("unique", len(set(seen)))
print("load", open("/proc/loadavg").read().strip())
print("mem")
print(open("/proc/meminfo").read().splitlines()[0])
PY
echo === which enc ===
ls /oem/usr/bin/mpi_enc_test /oem/usr/bin/ffmpeg /usr/bin/ffmpeg 2>/dev/null
mpi_enc_test -h 2>&1 | head -40
""", wait=12))
