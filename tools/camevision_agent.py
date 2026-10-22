#!/usr/bin/env python3
"""CameVision Single recorder.

Card layout (camevision-session-1), one camera and one IMU:

    <card>/camevision/sessions/<id>/
        session.json
        imu0.csv
        cam0/video.mp4

video.mp4 is H.264 at the sensor's full frame (1920x1200 on SC233HGS,
1400x1600 on MIRA220). <id> is UTC, 20261023T160102Z. IMU columns are
t_unix_ns,t_mono_ns,ax,ay,az,gx,gy,gz with accel in m/s^2 and gyro in deg/s.

Bluetooth and HTTP speak the same JSON commands. The phone uses Bluetooth
to start, stop, preview, and clear. Online mode uploads from the camera
Wi-Fi to the server saved in /userdata/camevision-app.json. Standalone mode
leaves the files on the card so the phone can copy them and upload.
"""
from __future__ import print_function

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

try:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn

    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

PRODUCT = "CV-EGO01-SS"
PROFILE = "single"
FORMAT = "camevision-session-1"
HTTP_PORT = 8090
LIVE_JPG = os.environ.get("CAMEVISION_LIVE", "/tmp/camevision-live.jpg")
CFG_PATH = os.environ.get("CAMEVISION_CFG", "/userdata/camevision-app.json")
WPA_PATH = os.environ.get("CAMEVISION_WPA", "/userdata/wpa_camevision.conf")
CARD_STOP_FREE = 64 * 1024 * 1024
RECORD_FLAG = "/tmp/camevision-record.on"
RECORD_FIFO = "/tmp/camevision-nv12.fifo"
RECORD_GEOM = "/tmp/camevision-record.geom"
AIM_FLAG = "/tmp/camevision-aim.on"
AIM_JPG = "/tmp/camevision-aim.jpg"
VIDEO_BPS = "20000000"
SESSION_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")
REL_RE = re.compile(r"^(session\.json|imu0\.csv|cam0/video\.mp4)$")

AGENT = None


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def time_ns():
    fn = getattr(time, "time_ns", None)
    if fn:
        return int(fn())
    return int(time.time() * 1000000000)


def mono_ns():
    fn = getattr(time, "monotonic_ns", None)
    if fn:
        return int(fn())
    return int(time.monotonic() * 1000000000)


def iso_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def session_id_now():
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def load_cfg():
    cfg = {"server": "", "token": "", "warn": 85, "mode": "standalone"}
    try:
        with open(CFG_PATH, "r") as fh:
            got = json.load(fh)
        if isinstance(got, dict):
            cfg.update(got)
    except (OSError, ValueError):
        pass
    try:
        cfg["warn"] = int(cfg.get("warn") or 85)
    except (TypeError, ValueError):
        cfg["warn"] = 85
    if cfg.get("mode") not in ("standalone", "online"):
        cfg["mode"] = "standalone"
    return cfg


def save_cfg(cfg):
    parent = os.path.dirname(CFG_PATH)
    if parent and not os.path.isdir(parent):
        return
    tmp = CFG_PATH + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(cfg, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, CFG_PATH)


def find_sd():
    forced = os.environ.get("CAMEVISION_SD")
    if forced:
        return forced
    best = None
    try:
        mounts = open("/proc/mounts", "r")
    except OSError:
        mounts = None
    if mounts:
        with mounts:
            for line in mounts:
                parts = line.split()
                if len(parts) < 3:
                    continue
                dev, mnt, fstype = parts[0], parts[1], parts[2]
                if fstype not in ("vfat", "exfat", "ext4", "ext3", "ext2", "f2fs"):
                    continue
                if mnt in ("/", "/oem", "/userdata", "/system", "/vendor"):
                    continue
                name = dev.rsplit("/", 1)[-1]
                disk = name.split("p", 1)[0]
                flag = "/sys/block/%s/removable" % disk
                try:
                    with open(flag, "r") as fh:
                        if fh.read().strip() == "1":
                            return mnt
                except OSError:
                    pass
                if best is None:
                    best = mnt
    if best:
        return best
    for cand in ("/mnt/sdcard", "/mnt/extsd", "/media/sdcard", "/mnt/mmc"):
        if os.path.isdir(cand):
            return cand
    return None


def disk_of(path):
    if not path or not os.path.isdir(path) or not hasattr(os, "statvfs"):
        if path and os.path.isdir(path):
            return {"total": 0, "used": 0, "free": 0}
        return None
    try:
        st = os.statvfs(path)
    except OSError:
        return None
    total = int(st.f_blocks) * int(st.f_frsize)
    free = int(st.f_bavail) * int(st.f_frsize)
    used = total - (int(st.f_bfree) * int(st.f_frsize))
    if used < 0:
        used = 0
    return {"total": total, "used": used, "free": free}


def jpeg_size(data):
    i = 0
    limit = len(data) - 9
    while i < limit:
        if data[i] == 0xFF and data[i + 1] in (0xC0, 0xC1, 0xC2):
            height = (data[i + 5] << 8) | data[i + 6]
            width = (data[i + 7] << 8) | data[i + 8]
            return int(width), int(height)
        i += 1
    return 0, 0


def read_aim_jpeg():
    try:
        with open(AIM_JPG, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    if len(data) < 4 or len(data) > 16000:
        return None
    if data[0] != 0xFF or data[1] != 0xD8 or data[-2] != 0xFF or data[-1] != 0xD9:
        return None
    return data


def scan_wifi():
    try:
        subprocess.check_call(
            ["wpa_cli", "-i", "wlan0", "scan"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=4,
        )
    except (OSError, subprocess.SubprocessError):
        pass
    time.sleep(1.6)
    try:
        out = subprocess.check_output(
            ["wpa_cli", "-i", "wlan0", "scan_results"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=4,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    best = {}
    for line in out.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("bssid"):
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        ssid = parts[4].strip()
        if not ssid or ssid == "\\x00":
            continue
        try:
            rssi = int(parts[2])
        except ValueError:
            continue
        flags = parts[3]
        prev = best.get(ssid)
        if prev is None or rssi > prev["rssi"]:
            best[ssid] = {
                "ssid": ssid,
                "rssi": rssi,
                "secure": ("WPA" in flags) or ("WEP" in flags),
            }
    items = list(best.values())
    items.sort(key=lambda item: item["rssi"], reverse=True)
    return items[:24]


def read_live_jpeg():
    try:
        with open(LIVE_JPG, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    if len(data) < 4 or data[0] != 0xFF or data[1] != 0xD8:
        return None
    if data[-2] != 0xFF or data[-1] != 0xD9:
        return None
    return data


def wpa_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "").replace("\r", "")


def write_wpa(ssid, psk):
    body = (
        "ctrl_interface=/var/run/wpa_supplicant\n"
        "update_config=0\n"
        "ap_scan=1\n"
        "\n"
        "network={\n"
        '\tssid="%s"\n'
        '\tpsk="%s"\n'
        "\tkey_mgmt=WPA-PSK\n"
        "\tproto=RSN\n"
        "\tpairwise=CCMP\n"
        "\tgroup=CCMP\n"
        "\tpriority=10\n"
        "\tscan_ssid=1\n"
        "}\n"
    ) % (wpa_escape(ssid), wpa_escape(psk))
    parent = os.path.dirname(WPA_PATH)
    if parent and not os.path.isdir(parent):
        return False
    tmp = WPA_PATH + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(body)
    os.replace(tmp, WPA_PATH)
    return True


def spawn_wifi():
    script = "/userdata/camevision-wifi.sh"
    if not os.path.isfile(script):
        return
    try:
        logf = open("/userdata/wifi-boot.log", "ab")
    except OSError:
        logf = subprocess.DEVNULL
    try:
        subprocess.Popen(
            ["setsid", "sh", script],
            stdin=subprocess.DEVNULL,
            stdout=logf,
            stderr=subprocess.STDOUT,
        )
    except OSError:
        subprocess.Popen(
            ["sh", script],
            stdin=subprocess.DEVNULL,
            stdout=logf,
            stderr=subprocess.STDOUT,
        )


def probe_net():
    state, ssid, ip = "down", "", ""
    try:
        out = subprocess.check_output(
            ["ip", "-4", "addr", "show", "wlan0"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=2,
        )
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                ip = line.split()[1].split("/")[0]
                state = "up"
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        out = subprocess.check_output(
            ["wpa_cli", "-i", "wlan0", "status"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=2,
        )
        wpa = ""
        for line in out.splitlines():
            if line.startswith("ssid="):
                ssid = line.split("=", 1)[1]
            elif line.startswith("wpa_state="):
                wpa = line.split("=", 1)[1]
        if wpa and wpa != "COMPLETED":
            state = "joining"
        elif wpa == "COMPLETED" and state != "up":
            state = "joining"
    except (OSError, subprocess.SubprocessError):
        pass
    return state, ssid, ip


def server_ready(url):
    url = (url or "").strip()
    return bool(url) and "server.example.com" not in url


class Recorder(object):
    def __init__(self, sd_root=None):
        self.sd_root = sd_root
        self.lock = threading.Lock()
        self.cfg = load_cfg()
        self.mode = self.cfg.get("mode") or "standalone"
        self.recording = False
        self.session_id = ""
        self.frames = 0
        self.imu_rows = 0
        self.bytes = 0
        self.started = ""
        self.stopped = ""
        self.width = 0
        self.height = 0
        self.fps = 30
        self.video_path = ""
        self.error = ""
        self.imu_hz = 0.0
        self._ts = None
        self._imu = None
        self._hz_n = 0
        self._hz_t = time.monotonic()
        self._meta_t = 0.0
        self.started_mono = 0.0

    def card_root(self):
        if self.sd_root:
            return self.sd_root
        return find_sd()

    def sessions_dir(self):
        root = self.card_root()
        if not root:
            return None
        return os.path.join(root, "camevision", "sessions")

    def disk(self):
        return disk_of(self.card_root())

    def start(self, mode=None):
        with self.lock:
            if self.recording:
                return {"ok": False, "error": "recording"}
            if mode in ("standalone", "online"):
                self.mode = mode
            root = self.sessions_dir()
            if not root:
                self.error = "no_card"
                return {"ok": False, "error": "no_card"}
            sid = session_id_now()
            base = os.path.join(root, sid)
            try:
                os.makedirs(os.path.join(base, "cam0"))
                self.video_path = os.path.join(base, "cam0", "video.mp4")
                self._imu = open(os.path.join(base, "imu0.csv"), "w", newline="\n")
                self._imu.write("t_unix_ns,t_mono_ns,ax,ay,az,gx,gy,gz\n")
            except OSError:
                self._close_files()
                self.error = "no_card"
                return {"ok": False, "error": "no_card"}
            self.session_id = sid
            self.frames = 0
            self.imu_rows = 0
            self.bytes = 0
            self.width = 0
            self.height = 0
            self.fps = 30
            self.started = iso_now()
            self.stopped = ""
            self.started_mono = time.monotonic()
            self._hz_n = 0
            self._hz_t = time.monotonic()
            self.error = ""
            self.recording = True
            self._write_meta_locked(False)
            log("record %s %s" % (self.mode, sid))
            return {"ok": True, "error": "", "session": sid}

    def stop(self):
        with self.lock:
            if not self.recording:
                return {"ok": True, "error": ""}
            self.recording = False
            self.stopped = iso_now()
            self._close_files()
            self._write_meta_locked(True)
            log("stop %s frames=%s imu=%s" % (self.session_id, self.frames, self.imu_rows))
            return {"ok": True, "error": "", "session": self.session_id}

    def note_video(self, width, height, fps, size):
        with self.lock:
            if width:
                self.width = int(width)
            if height:
                self.height = int(height)
            if fps:
                self.fps = int(fps)
            self.bytes = int(size or 0)
            if self.session_id:
                self._write_meta_locked(not self.recording)

    def add_frame(self, jpeg, t_unix, t_mono):
        return False

    def add_imu(self, t_unix, t_mono, ax, ay, az, gx, gy, gz):
        with self.lock:
            if not self.recording or self._imu is None:
                return
            self._imu.write(
                "%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n"
                % (int(t_unix), int(t_mono), ax, ay, az, gx, gy, gz)
            )
            self.imu_rows += 1
            self._hz_n += 1
            now = time.monotonic()
            if now - self._hz_t >= 1.0:
                self.imu_hz = self._hz_n / (now - self._hz_t)
                self._hz_n = 0
                self._hz_t = now
            if self.imu_rows % 200 == 0:
                self._imu.flush()

    def clear(self):
        with self.lock:
            if self.recording:
                return {"ok": False, "error": "recording"}
            base = self.sessions_dir()
            if not base or not os.path.isdir(base):
                self.error = ""
                return {"ok": True, "error": ""}
            for name in list(os.listdir(base)):
                path = os.path.join(base, name)
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except OSError:
                    return {"ok": False, "error": "no_card"}
            self.session_id = ""
            self.frames = 0
            self.error = ""
            log("card cleared")
            return {"ok": True, "error": ""}

    def delete(self, sid):
        with self.lock:
            if self.recording and sid == self.session_id:
                return {"ok": False, "error": "recording"}
            path = self._session_path(sid)
            if not path or not os.path.isdir(path):
                return {"ok": False, "error": "bad_session"}
            shutil.rmtree(path)
            return {"ok": True, "error": ""}

    def mark(self, sid):
        with self.lock:
            path = self._session_path(sid)
            if not path or not os.path.isdir(path):
                return {"ok": False, "error": "bad_session"}
            with open(os.path.join(path, "SENT"), "w") as fh:
                fh.write("1\n")
            return {"ok": True, "error": ""}

    def note_sent(self, sid, rel):
        with self.lock:
            path = self._session_path(sid)
            if not path:
                return
            with open(os.path.join(path, ".sent"), "a") as fh:
                fh.write(rel + "\n")

    def read_sent(self, sid):
        path = self._session_path(sid)
        if not path:
            return set()
        try:
            with open(os.path.join(path, ".sent"), "r") as fh:
                return set(line.strip() for line in fh if line.strip())
        except OSError:
            return set()

    def unsent(self, sid):
        with self.lock:
            if self.recording and sid == self.session_id:
                return []
        sent = self.read_sent(sid)
        rel = "cam0/video.mp4"
        path = self.file_path(sid, rel)
        if not path or not os.path.isfile(path):
            return []
        try:
            if os.path.getsize(path) <= 0 or rel in sent:
                return []
        except OSError:
            return []
        return [rel]

    def file_path(self, sid, rel):
        if not SESSION_RE.match(sid or "") or not REL_RE.match(rel or ""):
            return None
        base = self._session_path(sid)
        if not base:
            return None
        path = os.path.realpath(os.path.join(base, rel.replace("/", os.sep)))
        root = os.path.realpath(base)
        if path != root and not path.startswith(root + os.sep):
            return None
        return path

    def list_sessions(self):
        base = self.sessions_dir()
        if not base or not os.path.isdir(base):
            return []
        items = []
        try:
            names = os.listdir(base)
        except OSError:
            return []
        for name in names:
            if not SESSION_RE.match(name):
                continue
            meta = {}
            try:
                with open(os.path.join(base, name, "session.json"), "r") as fh:
                    meta = json.load(fh)
            except (OSError, ValueError):
                meta = {}
            items.append(
                {
                    "id": name,
                    "frames": int(meta.get("frames") or 0),
                    "bytes": int(meta.get("bytes") or 0),
                    "mode": meta.get("mode") or "",
                    "started": meta.get("started") or "",
                    "sent": os.path.isfile(os.path.join(base, name, "SENT")),
                }
            )
        items.sort(key=lambda item: item["id"], reverse=True)
        return items

    def newest_id(self):
        items = self.list_sessions()
        if self.session_id:
            return self.session_id
        return items[0]["id"] if items else ""

    def _session_path(self, sid):
        if not SESSION_RE.match(sid or ""):
            return None
        base = self.sessions_dir()
        if not base:
            return None
        return os.path.join(base, sid)

    def _close_files(self):
        for fh in (self._ts, self._imu):
            if fh is not None:
                try:
                    fh.flush()
                    fh.close()
                except OSError:
                    pass
        self._ts = None
        self._imu = None

    def _write_meta_locked(self, final):
        path = self._session_path(self.session_id)
        if not path:
            return
        doc = {
            "format": FORMAT,
            "product": PRODUCT,
            "profile": PROFILE,
            "id": self.session_id,
            "mode": self.mode,
            "started": self.started,
            "stopped": self.stopped or None,
            "camera": {
                "id": "cam0",
                "width": self.width,
                "height": self.height,
                "fps": self.fps,
                "encoding": "h264",
                "container": "mp4",
                "file": "cam0/video.mp4",
            },
            "imu": {
                "id": "imu0",
                "accel_unit": "m/s^2",
                "gyro_unit": "deg/s",
            },
            "frames": self.frames,
            "imu_rows": self.imu_rows,
            "bytes": self.bytes,
        }
        tmp = os.path.join(path, "session.json.tmp")
        with open(tmp, "w") as fh:
            json.dump(doc, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, os.path.join(path, "session.json"))
        self._meta_t = time.monotonic()
        if final:
            done = os.path.join(path, "COMPLETE")
            if not self.recording:
                pass


def snapshot(rec):
    disk = rec.disk()
    with rec.lock:
        recording = rec.recording
        mode = rec.mode
        sid = rec.session_id
        frames = rec.frames
        imu_hz = rec.imu_hz
        width = rec.width
        height = rec.height
        error = rec.error
        cfg = dict(rec.cfg)
        target = sid
    if not target:
        target = rec.newest_id()
    pending = len(rec.unsent(target)) if target else 0
    sent = len(rec.read_sent(target)) if target else 0
    total = int(disk["total"]) if disk else 0
    used = int(disk["used"]) if disk else 0
    free = int(disk["free"]) if disk else 0
    warn_at = int(cfg.get("warn") or 85)
    card = rec.card_root() is not None and os.path.isdir(rec.card_root() or "")
    sd_warn = bool(card and total > 0 and used * 100 >= warn_at * total)
    return {
        "t": "status",
        "recording": recording,
        "mode": mode,
        "session": sid,
        "frames": frames,
        "width": width,
        "height": height,
        "imu_hz": round(float(imu_hz), 1),
        "sd_total": total,
        "sd_used": used,
        "sd_free": free,
        "sd_warn": sd_warn,
        "card": bool(card),
        "pending": pending,
        "sent": sent,
        "error": error,
        "product": PRODUCT,
        "profile": PROFILE,
    }


class Agent(object):
    def __init__(self, sd_root=None):
        self.rec = Recorder(sd_root)
        self.stop_ev = threading.Event()
        self.listeners = []
        self.on_preview = None
        self.preview_until = 0.0
        self.upload_error = ""
        self._net = ("down", "", "")
        self._net_t = 0.0
        self._remote = set()
        self._completed = set()
        self._imu_post = {}
        self._live_started = False
        self.ff = None
        self._aim_on = False

    def emit(self, obj):
        raw = json.dumps(obj, separators=(",", ":")).encode("utf-8")
        for fn in list(self.listeners):
            try:
                fn(obj, raw)
            except Exception:
                pass

    def status(self):
        st = snapshot(self.rec)
        now = time.time()
        if now - self._net_t > 3:
            self._net = probe_net()
            self._net_t = now
        wifi, ssid, ip = self._net
        st["wifi"] = wifi
        st["ssid"] = ssid
        st["ip"] = ip
        st["preview"] = now < self.preview_until
        if self.upload_error and not st["error"]:
            st["error"] = self.upload_error
        return st

    def handle(self, cmd):
        if not isinstance(cmd, dict):
            result = {"ok": False, "error": "bad_cmd"}
            name = ""
        else:
            name = str(cmd.get("cmd") or "")
            result = self._dispatch(name, cmd)
        ack = {"t": "ack", "cmd": name, "ok": bool(result.get("ok")), "error": result.get("error") or ""}
        if result.get("session"):
            ack["session"] = result["session"]
        self.emit(ack)
        self.emit(self.status())
        if name == "list":
            self.emit({"t": "sessions", "items": self.rec.list_sessions()})
        return result

    def _dispatch(self, name, cmd):
        if name in ("hello", "ping"):
            return {
                "ok": True,
                "error": "",
                "t": "hello",
                "product": PRODUCT,
                "name": "CameVision Ego Single",
                "protocol": 1,
            }
        if name == "start":
            return self.rec.start(cmd.get("mode"))
        if name == "stop":
            self.stop_video()
            return self.rec.stop()
        if name == "mode":
            return self._set_mode(cmd.get("mode"))
        if name == "preview":
            try:
                seconds = int(cmd.get("seconds") or 0)
            except (TypeError, ValueError):
                seconds = 0
            if seconds <= 0:
                self.preview_until = 0
                self.set_aim(False)
            else:
                self.preview_until = time.time() + min(seconds, 4)
                self.set_aim(True)
            return {"ok": True, "error": ""}
        if name == "clear":
            return self.rec.clear()
        if name == "delete":
            return self.rec.delete(str(cmd.get("session") or ""))
        if name == "mark":
            return self.rec.mark(str(cmd.get("session") or ""))
        if name == "list":
            return {"ok": True, "error": ""}
        if name == "wifi":
            threading.Thread(target=self._emit_wifi, daemon=True).start()
            return {"ok": True, "error": ""}
        if name == "config":
            return self._config(cmd)
        return {"ok": False, "error": "bad_cmd"}

    def _set_mode(self, mode):
        with self.rec.lock:
            if self.rec.recording:
                return {"ok": False, "error": "recording"}
            if mode not in ("standalone", "online"):
                return {"ok": False, "error": "bad_mode"}
            self.rec.mode = mode
            self.rec.cfg["mode"] = mode
            cfg = dict(self.rec.cfg)
        try:
            save_cfg(cfg)
        except OSError:
            pass
        return {"ok": True, "error": ""}

    def _config(self, cmd):
        with self.rec.lock:
            if self.rec.recording:
                return {"ok": False, "error": "recording"}
            cfg = dict(self.rec.cfg)
        if "server" in cmd:
            cfg["server"] = str(cmd.get("server") or "")
        if "token" in cmd:
            cfg["token"] = str(cmd.get("token") or "")
        if "warn" in cmd:
            try:
                cfg["warn"] = max(50, min(99, int(cmd.get("warn"))))
            except (TypeError, ValueError):
                pass
        if cmd.get("mode") in ("standalone", "online"):
            cfg["mode"] = cmd.get("mode")
        try:
            save_cfg(cfg)
        except OSError:
            return {"ok": False, "error": "no_card"}
        ssid = str(cmd.get("ssid") or "")
        if ssid:
            try:
                write_wpa(ssid, str(cmd.get("psk") or ""))
            except OSError:
                return {"ok": False, "error": "wifi"}
            spawn_wifi()
            self._net_t = 0
        with self.rec.lock:
            self.rec.cfg = cfg
            if not self.rec.recording:
                self.rec.mode = cfg.get("mode") or self.rec.mode
        log("config saved")
        return {"ok": True, "error": ""}

    def ensure_live(self):
        if self._live_started or read_live_jpeg():
            return
        script = "/userdata/single_live.py"
        if not os.path.isfile(script):
            return
        try:
            out = subprocess.check_output(["ps"], universal_newlines=True, timeout=3)
        except (OSError, subprocess.SubprocessError):
            out = ""
        if "single_live" in out:
            self._live_started = True
            return
        try:
            logf = open("/userdata/single-live.log", "ab")
            subprocess.Popen(
                ["python3", script],
                stdin=subprocess.DEVNULL,
                stdout=logf,
                stderr=subprocess.STDOUT,
            )
            self._live_started = True
            log("started single_live")
        except OSError:
            pass

    def loop_record(self):
        while not self.stop_ev.is_set():
            if not self.rec.recording:
                self.stop_video()
                time.sleep(0.1)
                continue
            disk = self.rec.disk()
            if disk and disk["total"] and disk["free"] < CARD_STOP_FREE:
                self.stop_video()
                self.rec.error = "card_full"
                self.rec.stop()
                self.emit(self.status())
                continue
            self.ensure_live()
            if self.ff is None:
                self.start_video()
            else:
                self.poll_video()
            time.sleep(0.3)

    def start_video(self):
        path = getattr(self.rec, "video_path", "") or ""
        if not path or self.ff is not None:
            return
        try:
            if not os.path.exists(RECORD_FIFO):
                os.mkfifo(RECORD_FIFO)
        except OSError:
            pass
        try:
            with open(RECORD_FLAG, "w") as fh:
                fh.write("1\n")
        except OSError:
            self.rec.error = "no_image"
            return
        geom = self.wait_geom()
        if not geom:
            self.clear_record_flag()
            if self.rec.recording:
                self.rec.error = "no_image"
            return
        width, height, fps = geom
        proc = self.launch_ffmpeg(path, width, height, fps)
        if proc is None:
            self.clear_record_flag()
            self.rec.error = "no_image"
            return
        self.ff = proc
        self.rec.note_video(width, height, fps, 0)
        log("video %sx%s @%s" % (width, height, fps))

    def wait_geom(self):
        deadline = time.time() + 8
        while time.time() < deadline and self.rec.recording and not self.stop_ev.is_set():
            try:
                with open(RECORD_GEOM, "r") as fh:
                    parts = fh.read().split()
                if len(parts) >= 2:
                    width = int(parts[0])
                    height = int(parts[1])
                    fps = int(parts[2]) if len(parts) > 2 else 30
                    if width > 0 and height > 0:
                        return width, height, fps or 30
            except (OSError, ValueError):
                pass
            time.sleep(0.1)
        return None

    def ffmpeg_bin(self):
        for cand in ("/oem/usr/bin/ffmpeg", "/usr/bin/ffmpeg"):
            if os.path.isfile(cand):
                return cand
        return "ffmpeg"

    def encoder_args(self, binary):
        try:
            out = subprocess.check_output(
                [binary, "-hide_banner", "-encoders"],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=6,
            )
        except (OSError, subprocess.SubprocessError):
            out = ""
        if "h264_rkmpp" in out:
            return ["-c:v", "h264_rkmpp", "-b:v", VIDEO_BPS]
        if "h264_v4l2m2m" in out:
            return ["-c:v", "h264_v4l2m2m", "-b:v", VIDEO_BPS]
        return ["-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-crf", "18"]

    def launch_ffmpeg(self, path, width, height, fps):
        binary = self.ffmpeg_bin()
        cmd = [
            binary, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "nv12",
            "-s", "%dx%d" % (width, height), "-r", str(fps),
            "-i", RECORD_FIFO,
        ]
        cmd.extend(self.encoder_args(binary))
        cmd.extend([
            "-pix_fmt", "yuv420p",
            "-movflags", "frag_keyframe+empty_moov+default_base_moof",
            path,
        ])
        try:
            logf = open("/userdata/camevision-video.log", "ab")
        except OSError:
            logf = subprocess.DEVNULL
        try:
            return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=logf, stderr=subprocess.STDOUT)
        except OSError as exc:
            log("ffmpeg %s" % exc)
            return None

    def poll_video(self):
        proc = self.ff
        if proc is None:
            return
        if proc.poll() is not None:
            self.ff = None
            self.clear_record_flag()
            if self.rec.recording:
                self.rec.error = "no_image"
            return
        path = getattr(self.rec, "video_path", "") or ""
        try:
            size = os.path.getsize(path) if path else 0
        except OSError:
            size = 0
        self.rec.note_video(self.rec.width, self.rec.height, self.rec.fps, size)

    def stop_video(self):
        self.clear_record_flag()
        proc = self.ff
        self.ff = None
        if proc is None:
            return
        try:
            if proc.stdin:
                proc.stdin.write(b"q")
                proc.stdin.flush()
        except OSError:
            pass
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
        path = getattr(self.rec, "video_path", "") or ""
        try:
            size = os.path.getsize(path) if path else 0
        except OSError:
            size = 0
        if size:
            self.rec.note_video(self.rec.width, self.rec.height, self.rec.fps, size)
        log("video stopped bytes=%s" % size)

    def clear_record_flag(self):
        try:
            os.remove(RECORD_FLAG)
        except OSError:
            pass

    def set_aim(self, on):
        if on and not self._aim_on:
            try:
                os.remove(AIM_JPG)
            except OSError:
                pass
            try:
                with open(AIM_FLAG, "w") as fh:
                    fh.write("1\n")
            except OSError:
                pass
            self._aim_on = True
        elif (not on) and self._aim_on:
            self._aim_on = False
            try:
                os.remove(AIM_FLAG)
            except OSError:
                pass

    def _emit_wifi(self):
        self.emit({"t": "wifi", "items": scan_wifi()})

    def loop_preview(self):
        last = None
        while not self.stop_ev.is_set():
            if time.time() >= self.preview_until:
                self.set_aim(False)
                last = None
                time.sleep(0.1)
                continue
            self.set_aim(True)
            self.ensure_live()
            jpg = read_aim_jpeg()
            fn = self.on_preview
            if jpg and jpg != last and fn:
                last = jpg
                try:
                    fn(jpg)
                except Exception:
                    pass
            time.sleep(0.35)

    def loop_status(self):
        last = ""
        while not self.stop_ev.wait(1.0):
            st = self.status()
            blob = json.dumps(st, sort_keys=True)
            if blob != last:
                last = blob
                self.emit(st)

    def loop_imu(self):
        try:
            imu = discover_imu()
        except Exception:
            imu = None
        if not imu:
            self.loop_imu_http()
            return
        stop = self.stop_ev
        latest = {"gx": None, "gy": None, "gz": None}

        def gyro():
            files, scale = imu["gyro"]
            while not stop.is_set():
                try:
                    vals = [read_raw(f) * scale for f in files]
                except (OSError, ValueError):
                    time.sleep(0.2)
                    continue
                latest["gx"], latest["gy"], latest["gz"] = vals

        threading.Thread(target=gyro, name="cv-gyro", daemon=True).start()
        files, scale = imu["accel"]
        while not stop.is_set():
            try:
                ax, ay, az = [read_raw(f) * scale for f in files]
            except (OSError, ValueError):
                time.sleep(0.2)
                continue
            if latest["gx"] is None:
                continue
            self.rec.add_imu(
                time_ns(),
                mono_ns(),
                ax,
                ay,
                az,
                latest["gx"],
                latest["gy"],
                latest["gz"],
            )

    def loop_imu_http(self):
        last = None
        while not self.stop_ev.is_set():
            if not self.rec.recording:
                time.sleep(0.2)
                continue
            try:
                raw = urllib.request.urlopen("http://127.0.0.1:8083/", timeout=0.5).read()
                doc = json.loads(raw.decode("utf-8"))
            except (OSError, urllib.error.URLError, ValueError):
                time.sleep(0.3)
                continue
            imu = doc.get("imu0") or {}
            stamp = doc.get("t_unix_ns")
            if stamp and stamp != last and "ax" in imu and "gx" in imu:
                last = stamp
                self.rec.add_imu(
                    stamp,
                    doc.get("t_mono_ns") or 0,
                    float(imu["ax"]),
                    float(imu["ay"]),
                    float(imu["az"]),
                    float(imu["gx"]),
                    float(imu["gy"]),
                    float(imu["gz"]),
                )
                try:
                    self.rec.imu_hz = float(doc.get("read_hz") or imu.get("read_hz") or 0)
                except (TypeError, ValueError):
                    pass
            time.sleep(0.01)

    def loop_upload(self):
        while not self.stop_ev.wait(1.0):
            if self.rec.mode != "online":
                continue
            cfg = self.rec.cfg
            server = str(cfg.get("server") or "").strip().rstrip("/")
            if not server_ready(server):
                self.upload_error = "server_template"
                continue
            sid = self.rec.session_id or self.rec.newest_id()
            if not sid:
                self.upload_error = ""
                continue
            try:
                self.upload_burst(server, str(cfg.get("token") or ""), sid)
                if self.upload_error == "upload_failed":
                    self.upload_error = ""
            except Exception as exc:
                self.upload_error = "upload_failed"
                log("upload %s" % type(exc).__name__)
                self.stop_ev.wait(3)

    def upload_burst(self, server, token, sid):
        self.ensure_remote(server, token, sid)
        self.post_file(server, token, sid, "session.json")
        deadline = time.time() + 2.5
        for rel in self.rec.unsent(sid):
            if time.time() > deadline or self.stop_ev.is_set():
                break
            self.post_file(server, token, sid, rel)
            self.rec.note_sent(sid, rel)
        last = self._imu_post.get(sid, 0)
        if time.time() - last > 5:
            self.post_file(server, token, sid, "imu0.csv")
            self._imu_post[sid] = time.time()
        if (not self.rec.recording) and sid not in self._completed and not self.rec.unsent(sid):
            self.post_json(server, token, server + "/sessions/" + sid + "/complete", {"id": sid})
            self._completed.add(sid)

    def ensure_remote(self, server, token, sid):
        if sid in self._remote:
            return
        body = {
            "id": sid,
            "product": PRODUCT,
            "profile": PROFILE,
            "format": FORMAT,
            "mode": self.rec.mode,
        }
        self.post_json(server, token, server + "/sessions", body)
        self._remote.add(sid)

    def post_file(self, server, token, sid, rel):
        path = self.rec.file_path(sid, rel)
        if not path or not os.path.isfile(path):
            return
        with open(path, "rb") as fh:
            data = fh.read()
        if rel.endswith(".mp4"):
            ctype = "video/mp4"
        elif rel.endswith(".json"):
            ctype = "application/json"
        else:
            ctype = "text/csv"
        url = "%s/sessions/%s/files" % (server, sid)
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", ctype)
        req.add_header("X-CameVision-Path", rel)
        req.add_header("X-CameVision-Session", sid)
        req.add_header("X-CameVision-Product", PRODUCT)
        req.add_header("User-Agent", "CameVision-Single")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            resp.read()
            resp.close()
        except urllib.error.HTTPError as exc:
            if exc.code not in (200, 201, 204):
                raise

    def post_json(self, server, token, url, body):
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-CameVision-Product", PRODUCT)
        req.add_header("User-Agent", "CameVision-Single")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        try:
            resp = urllib.request.urlopen(req, timeout=20)
            resp.read()
            resp.close()
        except urllib.error.HTTPError as exc:
            if exc.code not in (200, 201, 204, 409):
                raise

    def start_threads(self):
        threads = (
            ("cv-record", self.loop_record),
            ("cv-preview", self.loop_preview),
            ("cv-status", self.loop_status),
            ("cv-imu", self.loop_imu),
            ("cv-upload", self.loop_upload),
            ("cv-http", self.loop_http),
            ("cv-ble", self.loop_ble),
        )
        for name, fn in threads:
            threading.Thread(target=fn, name=name, daemon=True).start()
        log("agent up port=%s" % HTTP_PORT)

    def loop_http(self):
        try:
            httpd = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler)
        except OSError as exc:
            log("HTTP off %s" % exc)
            return
        httpd.serve_forever()

    def loop_ble(self):
        try:
            import camevision_ble
        except Exception as exc:
            log("BLE import %s" % exc)
            return
        try:
            camevision_ble.serve(self)
        except Exception as exc:
            log("BLE off %s" % exc)

    def shutdown(self):
        self.stop_ev.set()
        self.preview_until = 0
        self.set_aim(False)
        self.stop_video()
        try:
            self.rec.stop()
        except Exception:
            pass


def read_raw(fh):
    fh.seek(0)
    return int((fh.read().strip() or b"0"))


def open_raw(path):
    return open(path, "rb", buffering=0)


def discover_imu():
    root = "/sys/bus/iio/devices"
    if not os.path.isdir(root):
        return None
    accel = gyro = None
    for name in sorted(os.listdir(root)):
        dev = os.path.join(root, name)
        try:
            with open(os.path.join(dev, "name"), "r") as fh:
                label = fh.read().strip().lower()
        except OSError:
            continue
        if "lsm6" not in label and "accel" not in label and "gyro" not in label and "anglvel" not in label:
            continue
        if os.path.isfile(os.path.join(dev, "in_accel_x_raw")):
            accel = dev
        if os.path.isfile(os.path.join(dev, "in_anglvel_x_raw")):
            gyro = dev
    if not accel or not gyro:
        return None
    try:
        with open(os.path.join(accel, "sampling_frequency"), "w") as fh:
            fh.write("480")
        with open(os.path.join(gyro, "sampling_frequency"), "w") as fh:
            fh.write("480")
    except OSError:
        pass
    with open(os.path.join(accel, "in_accel_scale"), "r") as fh:
        ascale = float(fh.read().strip())
    with open(os.path.join(gyro, "in_anglvel_scale"), "r") as fh:
        gscale = float(fh.read().strip()) * 57.29577951308232
    return {
        "accel": (
            (
                open_raw(os.path.join(accel, "in_accel_x_raw")),
                open_raw(os.path.join(accel, "in_accel_y_raw")),
                open_raw(os.path.join(accel, "in_accel_z_raw")),
            ),
            ascale,
        ),
        "gyro": (
            (
                open_raw(os.path.join(gyro, "in_anglvel_x_raw")),
                open_raw(os.path.join(gyro, "in_anglvel_y_raw")),
                open_raw(os.path.join(gyro, "in_anglvel_z_raw")),
            ),
            gscale,
        ),
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        agent = AGENT
        if agent is None:
            self._json(503, {"ok": False, "error": "down"})
            return
        path = self.path.split("?", 1)[0]
        if path == "/v1/status":
            self._json(200, agent.status())
            return
        if path == "/v1/sessions":
            self._json(200, {"items": agent.rec.list_sessions()})
            return
        if path == "/v1/preview.jpg":
            jpg = read_live_jpeg()
            if not jpg:
                self._json(404, {"ok": False, "error": "no_image"})
                return
            self._bytes(200, "image/jpeg", jpg)
            return
        if path == "/v1/preview.mjpg":
            self._mjpeg()
            return
        rel = self._session_rel(path)
        if rel:
            sid, name = rel
            file_path = agent.rec.file_path(sid, name)
            if not file_path or not os.path.isfile(file_path):
                self._json(404, {"ok": False, "error": "bad_session"})
                return
            if name.endswith(".mp4"):
                ctype = "video/mp4"
            elif name.endswith(".json"):
                ctype = "application/json"
            else:
                ctype = "text/csv"
            with open(file_path, "rb") as fh:
                self._bytes(200, ctype, fh.read())
            return
        self._json(404, {"ok": False, "error": "bad_cmd"})

    def do_POST(self):
        agent = AGENT
        if agent is None:
            self._json(503, {"ok": False, "error": "down"})
            return
        path = self.path.split("?", 1)[0]
        if path != "/v1/cmd":
            self._json(404, {"ok": False, "error": "bad_cmd"})
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length else b"{}"
        try:
            cmd = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError):
            self._json(400, {"ok": False, "error": "bad_cmd"})
            return
        result = agent.handle(cmd)
        self._json(200, result)

    def _session_rel(self, path):
        prefix = "/v1/sessions/"
        if not path.startswith(prefix):
            return None
        rest = path[len(prefix):]
        if "/" not in rest:
            return None
        sid, rel = rest.split("/", 1)
        if not SESSION_RE.match(sid) or not REL_RE.match(rel):
            return None
        return sid, rel

    def _json(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self._bytes(code, "application/json", data)

    def _bytes(self, code, ctype, data):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _mjpeg(self):
        self.send_response(200)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()
        end = time.time() + 10
        last = None
        try:
            while time.time() < end:
                jpg = read_live_jpeg()
                if jpg and jpg != last:
                    last = jpg
                    head = b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(jpg)
                    self.wfile.write(head + jpg + b"\r\n")
                time.sleep(0.12)
        except OSError:
            return


def self_test():
    root = os.environ.get("CAMEVISION_SD")
    made = False
    if not root:
        import tempfile

        root = tempfile.mkdtemp(prefix="cv-session-")
        made = True
    try:
        rec = Recorder(root)
        ack = rec.start("standalone")
        if not ack.get("ok"):
            raise SystemExit("start failed %s" % ack)
        with open(rec.video_path, "wb") as fh:
            fh.write(b"\x00\x00\x00\x18ftypmp42")
        rec.note_video(1920, 1200, 30, 24)
        rec.add_imu(1000, 2000, 0.0, 0.0, 9.8, 0.1, 0.2, 0.3)
        stopped = rec.stop()
        if not stopped.get("ok"):
            raise SystemExit("stop failed")
        sid = stopped["session"]
        base = os.path.join(root, "camevision", "sessions", sid)
        for rel in ("session.json", "imu0.csv", os.path.join("cam0", "video.mp4")):
            if not os.path.isfile(os.path.join(base, rel)):
                raise SystemExit("missing %s" % rel)
        with open(os.path.join(base, "session.json"), "r") as fh:
            meta = json.load(fh)
        cam = meta.get("camera") or {}
        if meta.get("format") != FORMAT or cam.get("encoding") != "h264":
            raise SystemExit("bad meta")
        if cam.get("width") != 1920 or cam.get("height") != 1200:
            raise SystemExit("not full resolution")
        if meta.get("imu_rows") != 1:
            raise SystemExit("bad counts")
        items = rec.list_sessions()
        if len(items) != 1 or items[0]["id"] != sid:
            raise SystemExit("list failed")
        cleared = rec.clear()
        if not cleared.get("ok") or rec.list_sessions():
            raise SystemExit("clear failed")
        print("SELF_TEST_OK", sid)
        return 0
    finally:
        if made:
            shutil.rmtree(root, ignore_errors=True)


def main(argv):
    global AGENT
    if "--self-test" in argv:
        return self_test()
    agent = Agent()
    AGENT = agent

    def _stop(signum, frame):
        log("signal %s" % signum)
        agent.shutdown()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _stop)
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, _stop)
    agent.start_threads()
    while not agent.stop_ev.is_set():
        time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
