#!/usr/bin/env python3
import sys
sys.path.insert(0, "/userdata")
from camevision_dbus import SystemBus

bus = SystemBus()
admgr = "org.bluez.LEAdvertisingManager1"
hci = "/org/bluez/hci0"


def get(prop):
    try:
        msg = bus.call("org.bluez", hci, "org.freedesktop.DBus.Properties", "Get", "ss", admgr, prop)
        print(prop, msg.values())
    except Exception as exc:
        print(prop, "ERR", exc)


get("ActiveInstances")
get("SupportedInstances")
get("SupportedIncludes")
get("SupportedSecondaryChannels")

for path in (
    "/org/bluez/advertising",
    "/org/bluez/advertising0",
    "/org/bluez/advertisement",
    "/eu/camemake/camevision/advert",
    "/org/bluez/example/advertisement0",
):
    try:
        bus.call("org.bluez", hci, admgr, "UnregisterAdvertisement", "o", path)
        print("unreg", path, "ok")
    except Exception as exc:
        print("unreg", path, exc)

get("ActiveInstances")

try:
    names = bus.call(
        "org.freedesktop.DBus",
        "/org/freedesktop/DBus",
        "org.freedesktop.DBus",
        "ListNames",
        "",
    )
    print("names", [n for n in names.values()[0] if "blue" in str(n).lower() or "came" in str(n).lower() or n.startswith(":")])
except Exception as exc:
    print("names", exc)
