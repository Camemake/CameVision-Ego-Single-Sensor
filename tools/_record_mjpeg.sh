#!/bin/sh
wget -q -O - --post-data='{"cmd":"start","mode":"standalone"}' --header='Content-Type: application/json' http://127.0.0.1:8090/v1/cmd
echo
sleep 4
wget -q -O - http://127.0.0.1:8090/v1/status
echo
ls -l /userdata/camevision-video.log
tail -15 /userdata/camevision-video.log
find /mnt/sdcard/camevision -type f -ls
wget -q -O - --post-data='{"cmd":"stop"}' --header='Content-Type: application/json' http://127.0.0.1:8090/v1/cmd
echo
sleep 2
find /mnt/sdcard/camevision -type f -ls
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo MJ
