#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_telnet import run
print(run(r"""
echo === ps ===
ps | grep -E 'hw_rtsp|isp_publish|v4l2-ctl|rkaiq_3A|mpi_enc' | grep -v grep
echo === files ===
ls -l /dev/shm/isp.nv12 /tmp/cam.nv12 /tmp/hw_one.h264 /userdata/v4l2-stream.log /userdata/hw-rtsp.log 2>/dev/null
echo === mtime loop ===
python3 - << 'PY'
import os, time
p="/dev/shm/isp.nv12"
for i in range(5):
    try:
        st=os.stat(p)
        print("i",i,"size",st.st_size,"mtime_ns",getattr(st,"st_mtime_ns",int(st.st_mtime*1e9)))
    except Exception as e:
        print("stat",e)
    time.sleep(0.4)
PY
echo === v4l2 log ===
tail -c 250 /userdata/v4l2-stream.log 2>/dev/null
echo === 3A ===
grep sysctl /userdata/rkaiq.log | tail -3
echo === fmt ===
v4l2-ctl -d /dev/video13 --get-fmt-video
""", wait=12))
