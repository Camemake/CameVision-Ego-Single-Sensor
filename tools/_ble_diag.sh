#!/bin/sh
echo '=== wlan ==='
ip -4 addr show wlan0 | grep inet || echo NO_WIFI
echo '=== procs ==='
ps | grep -E '[c]amevision_agent|[c]amevision_ble|[c]amevision-ble|[b]luetoothd|[s]kwbt' || true
echo '=== hci ==='
hciconfig -a 2>/dev/null || echo NO_HCI
echo '=== bt_service ==='
cat /proc/skwsdio/bt_service 2>/dev/null || echo NO_BT_SERVICE
echo '=== modules ==='
lsmod 2>/dev/null | grep -E 'skw|bt' || true
echo '=== agent log ==='
tail -30 /userdata/camevision-agent.log 2>/dev/null || tail -30 /tmp/camevision-agent.log 2>/dev/null || true
echo '=== ble adv log ==='
tail -20 /userdata/ble-adv.log 2>/dev/null || true
echo '=== wifi log ble ==='
grep -E 'BLE_|bt_service|skwbt' /userdata/camevision-wifi.log 2>/dev/null | tail -20
echo BLE_DIAG
