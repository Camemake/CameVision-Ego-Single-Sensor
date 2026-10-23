#!/usr/bin/env python3
"""Register a BlueZ LE advertisement named CameVision Ego Single + MAC."""
import sys

NAME = "CameVision Ego Single"

try:
    import dbus
    import dbus.exceptions
    import dbus.mainloop.glib
    import dbus.service
    from gi.repository import GLib
except Exception as exc:
    sys.stderr.write("ble-dbus-missing %s\n" % exc)
    sys.exit(2)

BLUEZ = "org.bluez"
LE_AD_MGR = "org.bluez.LEAdvertisingManager1"
LE_AD = "org.bluez.LEAdvertisement1"
DBUS_PROP = "org.freedesktop.DBus.Properties"


class Advertisement(dbus.service.Object):
    def __init__(self, bus, index, name):
        self.path = "/org/camevision/advertisement%d" % index
        self.bus = bus
        self.ad_type = "peripheral"
        self.local_name = name
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            LE_AD: {
                "Type": self.ad_type,
                "LocalName": dbus.String(self.local_name),
                "Discoverable": dbus.Boolean(True),
                "Includes": dbus.Array(["local-name"], signature="s"),
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        return self.get_properties()[LE_AD]

    @dbus.service.method(LE_AD, in_signature="", out_signature="")
    def Release(self):
        pass


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    ad = Advertisement(bus, 0, NAME)
    adapter = "/org/bluez/hci0"
    ad_mgr = dbus.Interface(bus.get_object(BLUEZ, adapter), LE_AD_MGR)
    ad_mgr.RegisterAdvertisement(ad.get_path(), {})
    sys.stdout.write("BLE_ADV_ON name=%s\n" % NAME)
    sys.stdout.flush()
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
