#!/bin/sh
echo '=== bins ==='
ls -l /oem/usr/bin/ffmpeg /usr/bin/ffmpeg 2>/dev/null
echo '=== encoders ==='
/usr/bin/ffmpeg -hide_banner -encoders 2>/dev/null | grep -iE 'h264|rkmpp|x264|mpeg4|mjpeg|jpeg'
echo '=== oem encoders ==='
/oem/usr/bin/ffmpeg -hide_banner -encoders 2>/dev/null | grep -iE 'h264|rkmpp|x264|mpeg4|mjpeg|jpeg'
echo FF
