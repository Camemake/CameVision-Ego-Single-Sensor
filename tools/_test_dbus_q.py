#!/usr/bin/env python3
from camevision_dbus import Message, Reader, Writer

w = Writer()
payload = b'{"cmd":"start","mode":"standalone","mtu":185}'
w.ay(payload)
w.dict_sv(
    {
        "offset": ("q", 0),
        "mtu": ("q", 517),
        "device": ("o", "/org/bluez/hci1/dev_7C33621405D2"),
        "type": ("s", "command"),
        "link": ("s", "le"),
    }
)
msg = Message()
msg.signature = "aya{sv}"
msg.body = bytes(w.buf)
vals = msg.values()
assert vals[0] == payload, vals[0]
opts = vals[1]
assert opts["mtu"][1] == 517, opts
assert opts["offset"][1] == 0, opts
print("WRITEVALUE_OK", vals[0], opts["mtu"], opts["offset"])
