#!/bin/sh
# Probe bluetoothctl advertise data syntax. Leave advertise on.
{
	printf '%s\n' \
		'menu advertise' \
		'data 0x09 43 61 6d 65 56 69 73 69 6f 6e 2d 34 36 32 43 34 37' \
		'data' \
		'name CameVision-462C47' \
		'name' \
		'back' \
		'advertise on'
	sleep 2
} | bluetoothctl
echo TRY
