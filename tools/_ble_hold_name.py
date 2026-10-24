#!/usr/bin/env python3
"""Hold one LE advert with the name in the primary extended PDU."""
import sys

sys.path.insert(0, "/userdata")
from camevision_dbus import SystemBus

SHORT = "CameVision-462C47"
PATH = "/eu/camemake/camevision/nameadv"
ADAPTER = "/org/bluez/hci0"


def mac_tail():
    try:
        import subprocess

        out = subprocess.check_output(["hciconfig", "hci0"], universal_newlines=True)
        for line in out.splitlines():
            if "BD Address" not in line:
                continue
            for part in line.split():
                if part.count(":") == 5:
                    return part.replace(":", "").upper()[-6:]
    except Exception:
        pass
    return "462C47"


def main():
    short = "CameVision-%s" % mac_tail()
    bus = SystemBus()
    props = {
        "Type": ("s", "peripheral"),
        "LocalName": ("s", short),
        "SecondaryChannel": ("s", "1M"),
    }

    def on_get_all(msg):
        bus.reply(msg, "a{sv}", props)

    def on_get(msg):
        vals = msg.values()
        _iface = vals[0] if vals else ""
        prop = vals[1] if len(vals) > 1 else ""
        got = props.get(prop)
        if got is None:
            bus.error(msg, "org.freedesktop.DBus.Error.InvalidArgs", prop)
            return
        bus.reply(msg, "v", got[0], got[1])

    def on_release(msg):
        print("ADV_RELEASE", flush=True)
        bus.reply(msg, "")

    bus.export(
        PATH,
        "org.freedesktop.DBus.Properties",
        {"GetAll": on_get_all, "Get": on_get},
    )
    bus.export(
        PATH,
        "org.bluez.LEAdvertisement1",
        {"Release": on_release, "GetAll": on_get_all, "Get": on_get},
    )
    bus.call(
        "org.bluez",
        ADAPTER,
        "org.bluez.LEAdvertisingManager1",
        "RegisterAdvertisement",
        "oa{sv}",
        PATH,
        {},
    )
    print("ADV_REG", short, flush=True)
    bus.loop()


if __name__ == "__main__":
    main()
