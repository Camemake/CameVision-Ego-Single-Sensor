#!/bin/sh
echo '=== ctl ==='
cat /tmp/camevision-uvc-ctl.json
echo
echo '=== bridge SET/PROBE ==='
grep -E 'SET |PROBE|STREAM' /userdata/cv-uvc-bridge.log | tail -40
echo
echo '=== live mira ==='
grep mira220 /userdata/single-live.log | tail -8
echo AFTER_DONE
