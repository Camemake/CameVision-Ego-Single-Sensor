#!/bin/sh
echo '=== preview.jpg ==='
wget -q -O /tmp/pv.jpg http://127.0.0.1:8090/v1/preview.jpg
ls -l /tmp/pv.jpg
echo '=== cmd preview ==='
wget -q -O - --post-data='{"cmd":"preview","seconds":10}' --header='Content-Type: application/json' http://127.0.0.1:8090/v1/cmd
echo
sleep 1
ls -l /tmp/camevision-aim.on /tmp/camevision-aim.jpg 2>/dev/null
echo '=== cmd start ==='
wget -q -O - --post-data='{"cmd":"start","mode":"standalone"}' --header='Content-Type: application/json' http://127.0.0.1:8090/v1/cmd
echo
sleep 3
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo '=== sessions ==='
ls -la /mnt/sdcard/camevision/sessions 2>/dev/null | head
echo '=== ffmpeg ==='
ls -l /oem/usr/bin/ffmpeg /usr/bin/ffmpeg 2>/dev/null
echo '=== agent ==='
tail -25 /userdata/camevision-agent.log
echo TRY
