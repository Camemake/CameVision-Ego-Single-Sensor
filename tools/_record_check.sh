#!/bin/sh
echo '=== video log ==='
cat /userdata/camevision-video.log 2>/dev/null | tail -30
echo '=== session ==='
find /mnt/sdcard/camevision -type f -ls 2>/dev/null
echo '=== flag geom fifo ==='
ls -l /tmp/camevision-record.on /tmp/camevision-record.geom /tmp/camevision-nv12.fifo 2>/dev/null
cat /tmp/camevision-record.geom 2>/dev/null
echo
echo '=== stop ==='
wget -q -O - --post-data='{"cmd":"stop"}' --header='Content-Type: application/json' http://127.0.0.1:8090/v1/cmd
echo
sleep 2
wget -q -O - http://127.0.0.1:8090/v1/status
echo
find /mnt/sdcard/camevision -type f -ls 2>/dev/null
echo CHK
