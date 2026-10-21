#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_telnet import run
print(run(r"""
export PATH=/oem/usr/bin:/usr/bin:/bin:$PATH
ls -l /userdata/isp_publish.py /userdata/hw_rtsp.py
# restart publisher only
if [ -f /tmp/isp-pub.pid ]; then kill $(cat /tmp/isp-pub.pid) 2>/dev/null; fi
for p in $(ps | grep isp_publish | grep -v grep | awk '{print $1}'); do kill $p; done
start-stop-daemon -S -b -q -m -p /tmp/isp-pub.pid -x /usr/bin/python3 -- /userdata/isp_publish.py
sleep 2
echo === after pub ===
ps | grep -E 'isp_publish|hw_rtsp|v4l2-ctl|rkaiq_3A' | grep -v grep
ls -l /dev/shm/isp.nv12
sleep 2
ls -l /dev/shm/isp.nv12
echo === rtsp log new ===
tail -c 180 /userdata/hw-rtsp.log
echo === pub log ===
# start-stop-daemon has no log; check fifo
ls -l /tmp/cam.nv12
""", wait=10))
