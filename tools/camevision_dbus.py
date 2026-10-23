#!/usr/bin/env python3
"""Minimal system-bus client. No dbus-python / gi — this rootfs has neither."""
from __future__ import print_function

import binascii
import os
import select
import socket
import struct
import threading
import time

METHOD_CALL = 1
METHOD_RETURN = 2
ERROR = 3
SIGNAL = 4

PATHS = (
    "/var/run/dbus/system_bus_socket",
    "/run/dbus/system_bus_socket",
)


def _next_sig(sig, i):
    if i >= len(sig):
        raise ValueError(sig)
    if sig[i] == "a":
        end = i + 1
        if end < len(sig) and sig[end] == "{":
            depth = 1
            end += 1
            while end < len(sig) and depth:
                if sig[end] == "{":
                    depth += 1
                elif sig[end] == "}":
                    depth -= 1
                end += 1
            return sig[i:end], end
        if end < len(sig) and sig[end] == "(":
            depth = 1
            end += 1
            while end < len(sig) and depth:
                if sig[end] == "(":
                    depth += 1
                elif sig[end] == ")":
                    depth -= 1
                end += 1
            return sig[i:end], end
        chunk, end = _next_sig(sig, end)
        return "a" + chunk, end
    return sig[i], i + 1


def _pack_args(w, signature, args):
    idx = 0
    i = 0
    while i < len(signature):
        chunk, i = _next_sig(signature, i)
        if chunk == "a{sv}":
            w.dict_sv(args[idx])
        elif chunk == "a{oa{sa{sv}}}":
            w.managed(args[idx])
        else:
            w.value(chunk, args[idx])
        idx += 1


def _pad(buf, n):
    while len(buf) % n:
        buf.append(0)


def _align(view, n):
    extra = (n - (view[1] % n)) % n
    view[1] += extra


class Writer(object):
    def __init__(self):
        self.buf = bytearray()

    def raw(self, data):
        self.buf.extend(data)

    def pad(self, n):
        _pad(self.buf, n)

    def y(self, v):
        self.buf.append(int(v) & 0xFF)

    def b(self, v):
        self.pad(4)
        self.buf.extend(struct.pack("<I", 1 if v else 0))

    def u(self, v):
        self.pad(4)
        self.buf.extend(struct.pack("<I", int(v) & 0xFFFFFFFF))

    def i(self, v):
        self.pad(4)
        self.buf.extend(struct.pack("<i", int(v)))

    def q(self, v):
        self.pad(2)
        self.buf.extend(struct.pack("<H", int(v) & 0xFFFF))

    def n(self, v):
        self.pad(2)
        self.buf.extend(struct.pack("<h", int(v)))

    def x(self, v):
        self.pad(8)
        self.buf.extend(struct.pack("<q", int(v)))

    def t(self, v):
        self.pad(8)
        self.buf.extend(struct.pack("<Q", int(v) & 0xFFFFFFFFFFFFFFFF))

    def s(self, v):
        data = v.encode("utf-8") if not isinstance(v, bytes) else v
        self.pad(4)
        self.buf.extend(struct.pack("<I", len(data)))
        self.buf.extend(data)
        self.buf.append(0)

    def o(self, v):
        self.s(v)

    def g(self, v):
        data = v.encode("ascii") if not isinstance(v, bytes) else v
        self.buf.append(len(data))
        self.buf.extend(data)
        self.buf.append(0)

    def ay(self, data):
        raw = bytes(bytearray(data))
        self.pad(4)
        self.buf.extend(struct.pack("<I", len(raw)))
        self.buf.extend(raw)

    def variant(self, sig, value):
        self.g(sig)
        self.value(sig, value)

    def value(self, sig, value):
        if sig == "y":
            self.y(value)
        elif sig == "b":
            self.b(value)
        elif sig == "u":
            self.u(value)
        elif sig == "i":
            self.i(value)
        elif sig == "q":
            self.q(value)
        elif sig == "n":
            self.n(value)
        elif sig == "x":
            self.x(value)
        elif sig == "t":
            self.t(value)
        elif sig == "s":
            self.s(value)
        elif sig == "o":
            self.o(value)
        elif sig == "g":
            self.g(value)
        elif sig == "ay":
            self.ay(value)
        elif sig == "as":
            self.array("s", value)
        elif sig == "ao":
            self.array("o", value)
        elif sig == "a{sv}":
            self.dict_sv(value)
        elif sig == "v":
            inner_sig, inner = value
            self.variant(inner_sig, inner)
        else:
            raise ValueError("pack %s" % sig)

    def array(self, elem, items):
        self.pad(4)
        mark = len(self.buf)
        self.buf.extend(b"\x00\x00\x00\x00")
        align = 8 if elem[:1] in "( {" else 4 if elem[:1] in "busoai" or elem == "b" else 1
        if elem in ("s", "o", "u", "b"):
            align = 4
        if elem.startswith("{") or elem.startswith("("):
            align = 8
        self.pad(align)
        start = len(self.buf)
        for item in items:
            self.value(elem, item)
        struct.pack_into("<I", self.buf, mark, len(self.buf) - start)

    def dict_sv(self, mapping):
        self.pad(4)
        mark = len(self.buf)
        self.buf.extend(b"\x00\x00\x00\x00")
        self.pad(8)
        start = len(self.buf)
        for key, (sig, val) in mapping.items():
            self.pad(8)
            self.s(key)
            self.variant(sig, val)
        struct.pack_into("<I", self.buf, mark, len(self.buf) - start)

    def ifaces(self, mapping):
        """a{sa{sv}} — interface name to property dict."""
        self.pad(4)
        mark = len(self.buf)
        self.buf.extend(b"\x00\x00\x00\x00")
        self.pad(8)
        start = len(self.buf)
        for iface, props in mapping.items():
            self.pad(8)
            self.s(iface)
            self.dict_sv(props)
        struct.pack_into("<I", self.buf, mark, len(self.buf) - start)

    def managed(self, objects):
        """a{oa{sa{sv}}} — GetManagedObjects body."""
        self.pad(4)
        mark = len(self.buf)
        self.buf.extend(b"\x00\x00\x00\x00")
        self.pad(8)
        start = len(self.buf)
        for path, ifaces in objects.items():
            self.pad(8)
            self.o(path)
            self.ifaces(ifaces)
        struct.pack_into("<I", self.buf, mark, len(self.buf) - start)


class Reader(object):
    def __init__(self, data, pos=0):
        self.data = data
        self.pos = pos

    def pad(self, n):
        self.pos += (n - (self.pos % n)) % n

    def y(self):
        v = self.data[self.pos]
        self.pos += 1
        return v

    def u(self):
        self.pad(4)
        v = struct.unpack_from("<I", self.data, self.pos)[0]
        self.pos += 4
        return v

    def i(self):
        self.pad(4)
        v = struct.unpack_from("<i", self.data, self.pos)[0]
        self.pos += 4
        return v

    def q(self):
        self.pad(2)
        v = struct.unpack_from("<H", self.data, self.pos)[0]
        self.pos += 2
        return v

    def n(self):
        self.pad(2)
        v = struct.unpack_from("<h", self.data, self.pos)[0]
        self.pos += 2
        return v

    def x(self):
        self.pad(8)
        v = struct.unpack_from("<q", self.data, self.pos)[0]
        self.pos += 8
        return v

    def t(self):
        self.pad(8)
        v = struct.unpack_from("<Q", self.data, self.pos)[0]
        self.pos += 8
        return v

    def b(self):
        return bool(self.u())

    def s(self):
        n = self.u()
        out = self.data[self.pos : self.pos + n]
        self.pos += n + 1
        return out.decode("utf-8")

    def o(self):
        return self.s()

    def g(self):
        n = self.y()
        out = self.data[self.pos : self.pos + n]
        self.pos += n + 1
        return out.decode("ascii")

    def ay(self):
        n = self.u()
        out = self.data[self.pos : self.pos + n]
        self.pos += n
        return bytes(out)

    def value(self, sig):
        if sig == "y":
            return self.y()
        if sig == "b":
            return self.b()
        if sig == "u":
            return self.u()
        if sig == "i":
            return self.i()
        if sig == "q":
            return self.q()
        if sig == "n":
            return self.n()
        if sig == "x":
            return self.x()
        if sig == "t":
            return self.t()
        if sig == "s":
            return self.s()
        if sig == "o":
            return self.o()
        if sig == "g":
            return self.g()
        if sig == "ay":
            return self.ay()
        if sig == "as":
            return self.array("s")
        if sig == "a{sv}":
            return self.dict_sv()
        if sig == "v":
            inner = self.g()
            return inner, self.value(inner)
        if sig.startswith("a"):
            return self.array(sig[1:])
        raise ValueError("unpack %s" % sig)

    def array(self, elem):
        n = self.u()
        align = 8 if elem[:1] in "({" else 4 if elem[:1] in "usob" else 1
        self.pad(align)
        end = self.pos + n
        out = []
        while self.pos < end:
            if elem.startswith("{") or elem.startswith("("):
                self.pad(8)
            out.append(self.value(elem))
        return out

    def dict_sv(self):
        n = self.u()
        self.pad(8)
        end = self.pos + n
        out = {}
        while self.pos < end:
            self.pad(8)
            key = self.s()
            out[key] = self.value("v")
        return out


class Message(object):
    def __init__(self):
        self.kind = 0
        self.serial = 0
        self.path = ""
        self.interface = ""
        self.member = ""
        self.destination = ""
        self.sender = ""
        self.signature = ""
        self.reply_serial = 0
        self.body = b""

    def values(self):
        if not self.signature:
            return []
        r = Reader(self.body)
        out = []
        i = 0
        sig = self.signature
        while i < len(sig):
            if sig[i] == "a":
                end = i + 1
                if end < len(sig) and sig[end] == "{":
                    depth = 1
                    end += 1
                    while end < len(sig) and depth:
                        if sig[end] == "{":
                            depth += 1
                        elif sig[end] == "}":
                            depth -= 1
                        end += 1
                elif end < len(sig) and sig[end] == "(":
                    depth = 1
                    end += 1
                    while end < len(sig) and depth:
                        if sig[end] == "(":
                            depth += 1
                        elif sig[end] == ")":
                            depth -= 1
                        end += 1
                else:
                    end += 1
                out.append(r.value(sig[i:end]))
                i = end
            elif sig[i] == "v":
                out.append(r.value("v"))
                i += 1
            else:
                out.append(r.value(sig[i]))
                i += 1
        return out


def _header(kind, serial, fields, body):
    field_w = Writer()
    for code, sig, val in fields:
        field_w.pad(8)
        field_w.y(code)
        field_w.variant(sig, val)
    field_bytes = bytes(field_w.buf)
    header = Writer()
    header.raw(b"l")
    header.y(kind)
    header.y(0)
    header.y(1)
    header.u(len(body))
    header.u(serial)
    header.u(len(field_bytes))
    header.raw(field_bytes)
    header.pad(8)
    return bytes(header.buf) + body


def parse_message(data):
    if len(data) < 16 or data[0:1] != b"l":
        raise ValueError("endian")
    kind = data[1]
    body_len = struct.unpack_from("<I", data, 4)[0]
    serial = struct.unpack_from("<I", data, 8)[0]
    fields_len = struct.unpack_from("<I", data, 12)[0]
    header_len = 16 + fields_len
    header_len += (8 - (header_len % 8)) % 8
    fields = Reader(data[16 : 16 + fields_len])
    msg = Message()
    msg.kind = kind
    msg.serial = serial
    msg.body = data[header_len : header_len + body_len]
    end = 16 + fields_len
    pos = 0
    blob = data[16:end]
    while pos < len(blob):
        pad = (8 - (pos % 8)) % 8
        pos += pad
        if pos >= len(blob):
            break
        r = Reader(blob, pos)
        code = r.y()
        sig = r.g()
        val = r.value(sig)
        pos = r.pos
        if code == 1:
            msg.path = val
        elif code == 2:
            msg.interface = val
        elif code == 3:
            msg.member = val
        elif code == 5:
            msg.reply_serial = val
        elif code == 6:
            msg.destination = val
        elif code == 7:
            msg.sender = val
        elif code == 8:
            msg.signature = val
    return msg, header_len + body_len


class SystemBus(object):
    def __init__(self):
        self.sock = None
        self.serial = 1
        self.unique = ""
        self.lock = threading.Lock()
        self.handlers = {}
        self.pending = {}
        self._connect()

    def _connect(self):
        last = None
        for path in PATHS:
            if not os.path.exists(path):
                continue
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(path)
            except OSError as exc:
                last = exc
                sock.close()
                continue
            self.sock = sock
            break
        if self.sock is None:
            raise RuntimeError("no system bus (%s)" % last)
        uid = binascii.hexlify(str(os.getuid()).encode())
        self.sock.sendall(b"\0AUTH EXTERNAL " + uid + b"\r\n")
        buf = b""
        while b"\r\n" not in buf:
            chunk = self.sock.recv(256)
            if not chunk:
                raise RuntimeError("dbus auth closed")
            buf += chunk
        if not buf.startswith(b"OK"):
            raise RuntimeError("dbus auth %s" % buf[:80])
        self.sock.sendall(b"BEGIN\r\n")
        reply = self.call(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus",
            "Hello",
            "",
        )
        self.unique = reply.values()[0] if reply.signature else ""

    def _next_serial(self):
        with self.lock:
            self.serial += 1
            return self.serial

    def send(self, kind, fields, body=b"", serial=None):
        if serial is None:
            serial = self._next_serial()
        raw = _header(kind, serial, fields, body)
        with self.lock:
            self.sock.sendall(raw)
        return serial

    def call(self, dest, path, iface, member, signature, *args, timeout=20):
        body = b""
        if signature:
            w = Writer()
            _pack_args(w, signature, args)
            body = bytes(w.buf)
        fields = [
            (1, "o", path),
            (2, "s", iface),
            (3, "s", member),
            (6, "s", dest),
        ]
        if signature:
            fields.append((8, "g", signature))
        serial = self.send(METHOD_CALL, fields, body)
        ev = threading.Event()
        box = {}
        self.pending[serial] = (ev, box)
        deadline = time.time() + timeout
        while serial in self.pending:
            if time.time() > deadline:
                self.pending.pop(serial, None)
                raise TimeoutError("%s.%s" % (iface, member))
            r, _, _ = select.select([self.sock], [], [], 0.2)
            if r:
                self.dispatch(self._read_one())
        msg = box.get("msg")
        if msg is None or msg.kind == ERROR:
            err = ""
            try:
                err = (msg.values()[0] if msg else "") or ""
            except Exception:
                err = ""
            raise RuntimeError("dbus %s.%s failed %s" % (iface, member, err))
        return msg

    def emit(self, path, iface, member, signature, *args):
        w = Writer()
        if signature == "sa{sv}as":
            w.s(args[0])
            w.dict_sv(args[1])
            w.array("s", args[2])
        elif signature:
            raise ValueError(signature)
        fields = [
            (1, "o", path),
            (2, "s", iface),
            (3, "s", member),
        ]
        if signature:
            fields.append((8, "g", signature))
        self.send(SIGNAL, fields, bytes(w.buf))

    def export(self, path, iface, methods):
        self.handlers[(path, iface)] = methods

    def reply(self, req, signature, *args):
        w = Writer()
        if signature == "a{oa{sa{sv}}}":
            w.managed(args[0])
        elif signature == "v":
            w.variant(args[0], args[1])
        elif signature:
            _pack_args(w, signature, args)
        fields = [
            (5, "u", req.serial),
            (6, "s", req.sender),
        ]
        if signature:
            fields.append((8, "g", signature))
        self.send(METHOD_RETURN, fields, bytes(w.buf))

    def error(self, req, name, text=""):
        w = Writer()
        w.s(text)
        fields = [
            (4, "s", name),
            (5, "u", req.serial),
            (6, "s", req.sender),
            (8, "g", "s"),
        ]
        self.send(ERROR, fields, bytes(w.buf))

    def _read_one(self):
        buf = b""
        while len(buf) < 16:
            chunk = self.sock.recv(16 - len(buf))
            if not chunk:
                raise RuntimeError("dbus closed")
            buf += chunk
        body_len = struct.unpack_from("<I", buf, 4)[0]
        fields_len = struct.unpack_from("<I", buf, 12)[0]
        header_len = 16 + fields_len
        header_len += (8 - (header_len % 8)) % 8
        need = header_len + body_len
        while len(buf) < need:
            chunk = self.sock.recv(need - len(buf))
            if not chunk:
                raise RuntimeError("dbus closed")
            buf += chunk
        msg, _n = parse_message(buf)
        return msg

    def dispatch(self, msg):
        if msg.kind in (METHOD_RETURN, ERROR):
            item = self.pending.pop(msg.reply_serial, None)
            if item:
                ev, box = item
                box["msg"] = msg
                ev.set()
            return
        if msg.kind != METHOD_CALL:
            return
        methods = self.handlers.get((msg.path, msg.interface))
        if methods is None and msg.interface == "org.freedesktop.DBus.Properties":
            # Properties live on every exported path.
            for (path, iface), fns in self.handlers.items():
                if path == msg.path and iface.endswith("1"):
                    methods = fns
                    break
        if not methods or msg.member not in methods:
            if msg.interface == "org.freedesktop.DBus.Introspectable" and msg.member == "Introspect":
                self.reply(msg, "s", '<node><interface name="org.freedesktop.DBus.Introspectable"><method name="Introspect"><arg type="s" direction="out"/></method></interface></node>')
                return
            self.error(msg, "org.freedesktop.DBus.Error.UnknownMethod", msg.member)
            return
        try:
            methods[msg.member](msg)
        except Exception as exc:
            print("DBUS_FAIL", msg.path, msg.member, msg.signature, exc, flush=True)
            self.error(msg, "org.bluez.Error.Failed", str(exc))

    def loop(self):
        while True:
            r, _, _ = select.select([self.sock], [], [], 0.25)
            if not r:
                continue
            self.dispatch(self._read_one())
