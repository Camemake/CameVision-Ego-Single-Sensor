#!/bin/sh
echo '=== alias ==='
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Name|Alias|ActiveInstances|Discoverable'
echo '=== newlog ==='
(logread 2>/dev/null || true) | grep -iE 'advert|Local name|parse_' | tail -10
echo LOG
