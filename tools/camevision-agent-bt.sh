#!/bin/sh
# Stay registered as the pairing agent so a phone tap is Just Works.
{
	printf '%s\n' \
		'agent NoInputNoOutput' \
		'default-agent' \
		'pairable on' \
		'discoverable on'
	sleep infinity
} | exec bluetoothctl
