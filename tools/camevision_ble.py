#!/usr/bin/env python3
"""CameVision BLE peripheral. BlueZ GATT, same JSON commands as HTTP /v1/cmd.

Service  6c9a0001-1a6f-4e84-8a00-63616d657631
Command  6c9a0002-1a6f-4e84-8a00-63616d657631   write
Info     6c9a0003-1a6f-4e84-8a00-63616d657631   notify
Frame    6c9a0004-1a6f-4e84-8a00-63616d657631   notify

Info packets: flags, msg id, utf-8. flags bit0 = first, bit1 = last.
Frame packets: seq, index, count as big-endian uint16, then JPEG bytes.
"""
from __future__ import print_function

import struct
import threading

SERVICE = "6c9a0001-1a6f-4e84-8a00-63616d657631"
COMMAND = "6c9a0002-1a6f-4e84-8a00-63616d657631"
INFO = "6c9a0003-1a6f-4e84-8a00-63616d657631"
FRAME = "6c9a0004-1a6f-4e84-8a00-63616d657631"
LOCAL_NAME = "CameVision Ego Single"

DBUS_PROP = "org.freedesktop.DBus.Properties"
DBUS_OM = "org.freedesktop.DBus.ObjectManager"
GATT_SVC = "org.bluez.GattService1"
GATT_CHR = "org.bluez.GattCharacteristic1"
AD_IFACE = "org.bluez.LEAdvertisement1"


def to_ay(data):
    import dbus

    return dbus.Array((dbus.Byte(b) for b in bytearray(data)), signature="y")


class Application(object):
    def __init__(self, bus, path):
        import dbus.service

        self.path = path
        self.services = []
        self._obj = dbus.service.Object.__init__  # keep import used by subclass
        dbus.service.Object.__init__(self, bus, path)

    def get_path(self):
        import dbus

        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)


def build(agent):
    import dbus
    import dbus.service

    class App(dbus.service.Object):
        def __init__(self, bus):
            self.path = "/eu/camemake/camevision"
            self.services = []
            dbus.service.Object.__init__(self, bus, self.path)

        def get_path(self):
            return dbus.ObjectPath(self.path)

        @dbus.service.method(DBUS_OM, out_signature="a{oa{sa{sv}}}")
        def GetManagedObjects(self):
            out = {}
            for service in self.services:
                out[service.get_path()] = service.get_properties()
                for char in service.chars:
                    out[char.get_path()] = char.get_properties()
            return out

    class Service(dbus.service.Object):
        def __init__(self, bus, index, uuid):
            self.path = "/eu/camemake/camevision/service%d" % index
            self.uuid = uuid
            self.chars = []
            dbus.service.Object.__init__(self, bus, self.path)

        def get_path(self):
            return dbus.ObjectPath(self.path)

        def add_char(self, char):
            self.chars.append(char)

        def get_properties(self):
            return {
                GATT_SVC: {
                    "UUID": self.uuid,
                    "Primary": dbus.Boolean(True),
                    "Characteristics": dbus.Array(
                        [char.get_path() for char in self.chars], signature="o"
                    ),
                }
            }

        @dbus.service.method(DBUS_PROP, in_signature="s", out_signature="a{sv}")
        def GetAll(self, interface):
            return self.get_properties()[GATT_SVC]

    class Char(dbus.service.Object):
        def __init__(self, bus, index, uuid, flags, service):
            self.path = service.path + "/char%d" % index
            self.uuid = uuid
            self.flags = flags
            self.service = service
            self.notifying = False
            self.value = []
            dbus.service.Object.__init__(self, bus, self.path)

        def get_path(self):
            return dbus.ObjectPath(self.path)

        def get_properties(self):
            return {
                GATT_CHR: {
                    "UUID": self.uuid,
                    "Service": self.service.get_path(),
                    "Flags": dbus.Array(self.flags, signature="s"),
                    "Notifying": dbus.Boolean(self.notifying),
                }
            }

        @dbus.service.method(DBUS_PROP, in_signature="s", out_signature="a{sv}")
        def GetAll(self, interface):
            return self.get_properties()[GATT_CHR]

        @dbus.service.method(GATT_CHR, in_signature="a{sv}", out_signature="ay")
        def ReadValue(self, options):
            return to_ay(self.value)

        @dbus.service.method(GATT_CHR, in_signature="aya{sv}")
        def WriteValue(self, value, options):
            pass

        @dbus.service.method(GATT_CHR)
        def StartNotify(self):
            self.notifying = True

        @dbus.service.method(GATT_CHR)
        def StopNotify(self):
            self.notifying = False

        @dbus.service.signal(DBUS_PROP, signature="sa{sv}as")
        def PropertiesChanged(self, interface, changed, invalidated):
            pass

        def notify(self, payload):
            if not self.notifying:
                return
            self.value = payload
            self.PropertiesChanged(GATT_CHR, {"Value": to_ay(payload)}, [])

    class CommandChar(Char):
        def __init__(self, bus, service, bridge):
            Char.__init__(self, bus, 0, COMMAND, ["write", "write-without-response"], service)
            self.bridge = bridge

        def WriteValue(self, value, options):
            data = bytes(bytearray(value))
            try:
                mtu = int(options.get("mtu") or 23)
            except (TypeError, ValueError):
                mtu = 23
            self.bridge.mtu = max(self.bridge.mtu, mtu)
            self.bridge.on_command(data)

    class InfoChar(Char):
        def __init__(self, bus, service):
            Char.__init__(self, bus, 1, INFO, ["read", "notify"], service)

    class FrameChar(Char):
        def __init__(self, bus, service):
            Char.__init__(self, bus, 2, FRAME, ["notify"], service)

    class Advertisement(dbus.service.Object):
        PATH = "/eu/camemake/camevision/advert"

        def __init__(self, bus):
            dbus.service.Object.__init__(self, bus, self.PATH)

        @dbus.service.method(AD_IFACE)
        def Release(self):
            pass

        @dbus.service.method(DBUS_PROP, in_signature="s", out_signature="a{sv}")
        def GetAll(self, interface):
            return {
                "Type": "peripheral",
                "ServiceUUIDs": dbus.Array([SERVICE], signature="s"),
                "LocalName": dbus.String(LOCAL_NAME),
                "IncludeTxPower": dbus.Boolean(True),
            }

    class Bridge(object):
        def __init__(self):
            self.mtu = 23
            self.info = None
            self.frame = None
            self.msg_id = 0
            self.seq = 0
            self.lock = threading.Lock()

        def on_command(self, data):
            try:
                import json

                cmd = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeError):
                return
            agent.handle(cmd)

        def send_info(self, _obj, raw):
            info = self.info
            if info is None:
                return
            room = max(12, self.mtu - 5)
            chunks = [raw[i : i + room] for i in range(0, len(raw), room)] or [b""]
            with self.lock:
                self.msg_id = (self.msg_id + 1) & 0xFF
                mid = self.msg_id
            last = len(chunks) - 1
            for index, chunk in enumerate(chunks):
                flags = 0
                if index == 0:
                    flags |= 1
                if index == last:
                    flags |= 2
                packet = bytes(bytearray([flags, mid])) + chunk
                self._notify(info, packet)

        def send_frame(self, jpg):
            frame = self.frame
            if frame is None or not jpg:
                return
            room = max(8, self.mtu - 3 - 6)
            count = (len(jpg) + room - 1) // room
            if count > 900 or len(jpg) > 16000:
                return
            with self.lock:
                self.seq = (self.seq + 1) & 0xFFFF
                seq = self.seq
            for index in range(count):
                part = jpg[index * room : (index + 1) * room]
                packet = struct.pack(">HHH", seq, index, count) + part
                self._notify(frame, packet)

        def _notify(self, char, packet):
            try:
                from gi.repository import GLib
            except Exception:
                char.notify(packet)
                return
            ev = threading.Event()

            def run():
                try:
                    char.notify(packet)
                finally:
                    ev.set()
                return False

            GLib.idle_add(run)
            ev.wait(0.4)

    bridge = Bridge()
    return App, Service, CommandChar, InfoChar, FrameChar, Advertisement, bridge


def _adapter(bus):
    import dbus

    root = dbus.Interface(bus.get_object("org.bluez", "/"), DBUS_OM)
    objects = root.GetManagedObjects()
    for path, ifaces in objects.items():
        if "org.bluez.GattManager1" in ifaces and "org.bluez.LEAdvertisingManager1" in ifaces:
            return path
    return None


def serve(agent):
    import dbus
    import dbus.mainloop.glib
    from gi.repository import GLib

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = _adapter(bus)
    if not adapter:
        raise RuntimeError("no hci adapter")
    props = dbus.Interface(bus.get_object("org.bluez", adapter), DBUS_PROP)
    props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(True))
    props.Set("org.bluez.Adapter1", "Alias", dbus.String(LOCAL_NAME))
    props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
    try:
        props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
    except dbus.exceptions.DBusException:
        pass

    App, Service, CommandChar, InfoChar, FrameChar, Advertisement, bridge = build(agent)
    app = App(bus)
    service = Service(bus, 0, SERVICE)
    command = CommandChar(bus, service, bridge)
    info = InfoChar(bus, service)
    frame = FrameChar(bus, service)
    bridge.info = info
    bridge.frame = frame
    service.add_char(command)
    service.add_char(info)
    service.add_char(frame)
    app.services.append(service)
    advert = Advertisement(bus)

    def on_info(_obj, raw):
        bridge.send_info(_obj, raw)

    agent.listeners.append(on_info)
    agent.on_preview = bridge.send_frame

    gatt = dbus.Interface(bus.get_object("org.bluez", adapter), "org.bluez.GattManager1")
    ads = dbus.Interface(bus.get_object("org.bluez", adapter), "org.bluez.LEAdvertisingManager1")
    gatt.RegisterApplication(app.get_path(), {}, timeout=30)
    try:
        ads.RegisterAdvertisement(advert.PATH, {}, timeout=30)
    except dbus.exceptions.DBusException as exc:
        print("advert", exc, flush=True)
    print("BLE_READY", LOCAL_NAME, flush=True)
    GLib.MainLoop().run()
