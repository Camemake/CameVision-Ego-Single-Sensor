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
import time

SERVICE = "6c9a0001-1a6f-4e84-8a00-63616d657631"
COMMAND = "6c9a0002-1a6f-4e84-8a00-63616d657631"
INFO = "6c9a0003-1a6f-4e84-8a00-63616d657631"
FRAME = "6c9a0004-1a6f-4e84-8a00-63616d657631"
def _hci_name():
    import os

    root = "/sys/class/bluetooth"
    if not os.path.isdir(root):
        return "hci0"
    names = [name for name in os.listdir(root) if name.startswith("hci")]
    # This combo chip often leaves a dead hci0 and a live hci1.
    if "hci1" in names:
        return "hci1"
    for name in sorted(names, reverse=True):
        try:
            with open(os.path.join(root, name, "address"), "r") as fh:
                addr = fh.read().strip().lower()
        except OSError:
            continue
        if addr and addr != "00:00:00:00:00:00":
            return name
    return names[0] if names else "hci0"


def _mac_tail():
    import os

    mac = ""
    hci = _hci_name()
    try:
        with open("/sys/class/bluetooth/%s/address" % hci, "r") as fh:
            mac = fh.read().strip().replace(":", "").upper()
    except OSError:
        mac = ""
    if len(mac) < 6 or mac == "000000000000":
        try:
            import subprocess

            out = subprocess.check_output(
                ["bluetoothctl", "show"], universal_newlines=True, timeout=3
            )
            for line in out.splitlines():
                if "Controller" in line and line.count(":") >= 5:
                    for part in line.split():
                        if part.count(":") == 5:
                            mac = part.replace(":", "").upper()
                            break
        except Exception:
            mac = ""
    return mac[-6:] if len(mac) >= 6 and mac != "000000" else ""


def display_name():
    tail = _mac_tail()
    if tail:
        return "CameVision Ego Single %s" % tail
    return "CameVision Ego Single"


def advert_name():
    """Short enough to fit in a 31-byte advert with the service UUID."""
    tail = _mac_tail()
    if tail:
        return "CameVision-%s" % tail
    return "CameVision"


LOCAL_NAME = display_name()

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
                "LocalName": dbus.String(advert_name()),
            }

    class Bridge(object):
        def __init__(self):
            self.mtu = 185
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
            if isinstance(cmd, dict):
                try:
                    got = int(cmd.get("mtu") or 0)
                except (TypeError, ValueError):
                    got = 0
                if 23 <= got <= 517:
                    agent.ble_mtu = got
            agent.handle(cmd)

        def send_info(self, _obj, raw):
            info = self.info
            if info is None:
                return
            self.mtu = max(23, min(int(self.mtu or 185), 185))
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
            att = max(23, min(int(self.mtu or 185), 185))
            self.mtu = att
            room = max(8, att - 3 - 6)
            count = (len(jpg) + room - 1) // room
            if count > 2500 or len(jpg) > 120000:
                return
            with self.lock:
                self.seq = (self.seq + 1) & 0xFFFF
                seq = self.seq
            for index in range(count):
                part = jpg[index * room : (index + 1) * room]
                packet = struct.pack(">HHH", seq, index, count) + part
                self._notify(frame, packet)
                time.sleep(0.001)

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

    prefer = "/org/bluez/" + _hci_name()
    root = dbus.Interface(bus.get_object("org.bluez", "/"), DBUS_OM)
    objects = root.GetManagedObjects()
    found = None
    for path, ifaces in objects.items():
        if "org.bluez.GattManager1" in ifaces and "org.bluez.LEAdvertisingManager1" in ifaces:
            if path == prefer:
                return path
            if found is None:
                found = path
    return found


def serve(agent):
    global LOCAL_NAME
    LOCAL_NAME = display_name()
    try:
        import dbus  # noqa: F401
        import dbus.mainloop.glib  # noqa: F401
        from gi.repository import GLib  # noqa: F401
    except Exception as exc:
        print("BLE_LITE", exc, flush=True)
        serve_lite(agent)
        return

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


def serve_lite(agent):
    """GATT + LE advert over the system bus without dbus-python."""
    from camevision_dbus import SystemBus

    app = "/eu/camemake/camevision"
    svc = app + "/service0"
    cmd_p = svc + "/char0"
    info_p = svc + "/char1"
    frame_p = svc + "/char2"
    info_d = info_p + "/desc0"
    frame_d = frame_p + "/desc0"
    adv = app + "/advert"
    CCCD = "00002902-0000-1000-8000-00805f9b34fb"
    adapter = "/org/bluez/" + _hci_name()
    name = display_name()
    short = advert_name()
    notifying = {info_p: True, frame_p: True}
    mtu = [185]
    bus = SystemBus()

    def _wait_adapter():
        import time

        last = None
        for _ in range(45):
            try:
                bus.call(
                    "org.bluez",
                    adapter,
                    "org.freedesktop.DBus.Properties",
                    "Get",
                    "ss",
                    "org.bluez.Adapter1",
                    "Powered",
                )
                return
            except Exception as exc:
                last = exc
                time.sleep(1)
        raise RuntimeError("hci0 not ready: %s" % last)

    _wait_adapter()

    def props_svc():
        return {
            "UUID": ("s", SERVICE),
            "Primary": ("b", True),
            "Characteristics": ("ao", [cmd_p, info_p, frame_p]),
        }

    def props_char(uuid, flags, descs=None):
        out = {
            "UUID": ("s", uuid),
            "Service": ("o", svc),
            "Flags": ("as", flags),
        }
        if descs:
            out["Descriptors"] = ("ao", descs)
        return out

    def props_desc(char_path):
        return {
            "UUID": ("s", CCCD),
            "Characteristic": ("o", char_path),
            "Flags": ("as", ["read", "write"]),
        }

    def props_adv():
        # No SecondaryChannel: this chip's extended-only PDUs are invisible
        # to Windows/Android legacy scanners. LocalName then goes in the
        # scan response, which a phone active scan can read.
        return {
            "Type": ("s", "peripheral"),
            "LocalName": ("s", short),
        }

    objects = {
        svc: {"org.bluez.GattService1": props_svc()},
        cmd_p: {
            "org.bluez.GattCharacteristic1": props_char(
                COMMAND, ["write", "write-without-response"]
            )
        },
        info_p: {
            "org.bluez.GattCharacteristic1": props_char(INFO, ["read", "notify"], [info_d])
        },
        frame_p: {
            "org.bluez.GattCharacteristic1": props_char(FRAME, ["notify"], [frame_d])
        },
        info_d: {"org.bluez.GattDescriptor1": props_desc(info_p)},
        frame_d: {"org.bluez.GattDescriptor1": props_desc(frame_p)},
        adv: {"org.bluez.LEAdvertisement1": props_adv()},
    }

    def on_managed(msg):
        gatt = dict((k, v) for k, v in objects.items() if k != adv)
        bus.reply(msg, "a{oa{sa{sv}}}", gatt)

    def on_get_all(msg):
        vals = msg.values()
        iface = vals[0] if vals else ""
        bus.reply(msg, "a{sv}", objects.get(msg.path, {}).get(iface, {}))

    def on_get(msg):
        vals = msg.values()
        iface = vals[0] if vals else ""
        prop = vals[1] if len(vals) > 1 else ""
        got = objects.get(msg.path, {}).get(iface, {}).get(prop)
        if got is None:
            bus.error(msg, "org.freedesktop.DBus.Error.InvalidArgs", prop)
            return
        bus.reply(msg, "v", got[0], got[1])

    def _as_bytes(raw):
        if raw is None:
            return b""
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        if isinstance(raw, list):
            try:
                return bytes(bytearray(raw))
            except Exception:
                return b""
        if isinstance(raw, str):
            return raw.encode("utf-8")
        return b""

    def on_write(msg):
        payload = b""
        opts = {}
        try:
            vals = msg.values()
            payload = _as_bytes(vals[0] if vals else b"")
            if len(vals) > 1 and isinstance(vals[1], dict):
                opts = vals[1]
        except Exception as exc:
            print("BLE_WRITE_PARSE", msg.signature, exc, flush=True)
            try:
                from camevision_dbus import Reader

                payload = _as_bytes(Reader(msg.body).ay())
            except Exception as exc2:
                print("BLE_WRITE_BODY", exc2, flush=True)
        if isinstance(opts, dict):
            got = opts.get("mtu")
            if got:
                try:
                    mtu[0] = max(mtu[0], int(got[1] if isinstance(got, tuple) else got))
                except (TypeError, ValueError, IndexError):
                    pass
        print("BLE_WRITE", msg.path, payload[:80], flush=True)
        if msg.path in (info_d, frame_d):
            parent = info_p if msg.path == info_d else frame_p
            notifying[parent] = True
            bus.reply(msg, "")
            return
        if msg.path == cmd_p:
            try:
                cmd = __import__("json").loads(payload.decode("utf-8"))
                if isinstance(cmd, dict):
                    try:
                        got = int(cmd.get("mtu") or 0)
                    except (TypeError, ValueError):
                        got = 0
                    if 23 <= got <= 517:
                        agent.ble_mtu = got
                agent.handle(cmd)
            except Exception as exc:
                print("BLE_CMD", exc, flush=True)
        bus.reply(msg, "")

    def on_read(msg):
        bus.reply(msg, "ay", b"")

    def on_start(msg):
        notifying[msg.path] = True
        print("BLE_NOTIFY_ON", msg.path, flush=True)
        bus.reply(msg, "")
        if msg.path == info_p:
            try:
                agent.handle({"cmd": "hello"})
            except Exception as exc:
                print("BLE_HELLO", exc, flush=True)

    def on_stop(msg):
        notifying[msg.path] = False
        bus.reply(msg, "")

    def on_release(msg):
        bus.reply(msg, "")

    bus.export(app, "org.freedesktop.DBus.ObjectManager", {"GetManagedObjects": on_managed})
    for path in (svc, cmd_p, info_p, frame_p, info_d, frame_d, adv):
        bus.export(
            path,
            "org.freedesktop.DBus.Properties",
            {"GetAll": on_get_all, "Get": on_get},
        )
    bus.export(
        svc,
        "org.bluez.GattService1",
        {"GetAll": on_get_all, "Get": on_get},
    )
    for path in (cmd_p, info_p, frame_p):
        bus.export(
            path,
            "org.bluez.GattCharacteristic1",
            {
                "ReadValue": on_read,
                "WriteValue": on_write,
                "StartNotify": on_start,
                "StopNotify": on_stop,
                "GetAll": on_get_all,
                "Get": on_get,
            },
        )
    for path in (info_d, frame_d):
        bus.export(
            path,
            "org.bluez.GattDescriptor1",
            {
                "ReadValue": on_read,
                "WriteValue": on_write,
                "GetAll": on_get_all,
                "Get": on_get,
            },
        )
    bus.export(adv, "org.bluez.LEAdvertisement1", {"Release": on_release, "GetAll": on_get_all})

    def notify(path, payload):
        notifying[path] = True
        bus.emit(
            path,
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            "sa{sv}as",
            "org.bluez.GattCharacteristic1",
            {"Value": ("ay", payload)},
            [],
        )

    class _LiteChar(object):
        def __init__(self, path):
            self.path = path

        def notify(self, payload):
            notify(self.path, payload)

    class _LiteBridge(object):
        def __init__(self):
            self.mtu = 185
            self.info = _LiteChar(info_p)
            self.frame = _LiteChar(frame_p)
            self.msg_id = 0
            self.seq = 0
            self.lock = threading.Lock()

        def _att(self):
            # This combo drops large notifies even when the phone claims 517.
            return max(23, min(int(mtu[0] or 185), 185))

        def send_info(self, _obj, raw):
            att = self._att()
            self.mtu = att
            room = max(12, att - 5)
            chunks = [raw[i : i + room] for i in range(0, len(raw), room)] or [b""]
            with self.lock:
                self.msg_id = (self.msg_id + 1) & 0xFF
                mid = self.msg_id
            last = len(chunks) - 1
            for index, chunk in enumerate(chunks):
                flags = (1 if index == 0 else 0) | (2 if index == last else 0)
                notify(info_p, bytes(bytearray([flags, mid])) + chunk)
                time.sleep(0.001)

        def send_frame(self, jpg):
            if not jpg:
                return
            att = self._att()
            self.mtu = att
            room = max(8, att - 3 - 6)
            count = (len(jpg) + room - 1) // room
            if count > 2500 or len(jpg) > 120000:
                print("BLE_FRAME_SKIP", len(jpg), "mtu", att, "n", count, flush=True)
                return
            print("BLE_FRAME", len(jpg), "mtu", att, "n", count, flush=True)
            with self.lock:
                self.seq = (self.seq + 1) & 0xFFFF
                seq = self.seq
            for index in range(count):
                part = jpg[index * room : (index + 1) * room]
                notify(frame_p, struct.pack(">HHH", seq, index, count) + part)
                time.sleep(0.001)

    lite = _LiteBridge()
    agent.listeners.append(lite.send_info)
    agent.on_preview = lite.send_frame

    def _set(prop, sig, val):
        try:
            bus.call(
                "org.bluez",
                adapter,
                "org.freedesktop.DBus.Properties",
                "Set",
                "ssv",
                "org.bluez.Adapter1",
                prop,
                (sig, val),
            )
        except Exception as exc:
            print("adapter %s %s" % (prop, exc), flush=True)

    _set("Powered", "b", True)
    _set("Alias", "s", short)
    # Default timeout is 180s. After that the phone Settings scan sees nothing.
    _set("DiscoverableTimeout", "u", 0)
    _set("Discoverable", "b", True)
    try:
        _set("Pairable", "b", True)
    except Exception:
        pass
    try:
        import subprocess

        # Imaging/camera, not Computer — phone Settings then says
        # "Can't communicate with Camevision" after a classic pair tap.
        hci = _hci_name()
        subprocess.call(["hciconfig", hci, "class", "0x000620"], timeout=3)
        subprocess.call(["hciconfig", hci, "piscan"], timeout=3)
        subprocess.call(["hciconfig", hci, "name", short], timeout=3)
    except Exception:
        pass

    bus.call(
        "org.bluez",
        adapter,
        "org.bluez.GattManager1",
        "RegisterApplication",
        "oa{sv}",
        app,
        {},
    )
    try:
        bus.call(
            "org.bluez",
            adapter,
            "org.bluez.LEAdvertisingManager1",
            "RegisterAdvertisement",
            "oa{sv}",
            adv,
            {},
        )
        print("ADV_REG", short, flush=True)
    except Exception as exc:
        print("advert", exc, flush=True)
    print("BLE_READY", name, "adv", short, flush=True)
    bus.loop()
