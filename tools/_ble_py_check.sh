#!/bin/sh
echo '=== py ==='
python3 -V
python3 -c 'import sys; print(sys.path)'
echo '=== imports ==='
python3 -c 'import gi; print("gi", gi.__file__)' 2>&1
python3 -c 'from gi.repository import GLib, Gio; print("gio-ok")' 2>&1
python3 -c 'import dbus' 2>&1
find /usr /oem /userdata -name 'dbus' -o -name '_dbus*.so' -o -name 'dbus.so' 2>/dev/null | head
echo '=== bluez tools ==='
command -v bluetoothctl; bluetoothctl --version 2>/dev/null
command -v btmgmt; command -v busctl; command -v gatt-server; command -v btgatt-server
ls /usr/libexec/bluetooth 2>/dev/null
echo '=== userdata py ==='
ls /userdata/*.py 2>/dev/null
echo PY_CHECK
