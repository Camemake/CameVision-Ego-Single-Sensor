#!/bin/sh
: > /userdata/camevision-video.log
wget -q -O - --post-data='{"cmd":"start","mode":"standalone"}' --header='Content-Type: application/json' http://127.0.0.1:8090/v1/cmd
echo
sleep 4
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo '=== cam0 ==='
ls /mnt/sdcard/camevision/sessions/*/cam0 2>/dev/null | head
echo '=== agent ==='
tail -12 /userdata/camevision-agent.log
wget -q -O - --post-data='{"cmd":"stop"}' --header='Content-Type: application/json' http://127.0.0.1:8090/v1/cmd
echo
sleep 1
echo '=== after stop ==='
ls /mnt/sdcard/camevision/sessions/*/cam0 2>/dev/null | head
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo JR
