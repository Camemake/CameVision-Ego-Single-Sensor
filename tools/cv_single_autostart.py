#!/usr/bin/env python3
"""Keep the Single live page up whenever the board is plugged in.

    python tools/cv_single_autostart.py --install
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_paths import GEN1_SERIAL, adb_exe, repo_root  # noqa: E402

ADB = adb_exe()
ROOT = repo_root()
LOG = ROOT / "build" / "single-autostart.log"
PIDF = ROOT / "build" / "single-autostart.pid"
PAGE = "http://127.0.0.1:8081/"


def log(msg: str) -> None:
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def adb(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run([ADB, *args], capture_output=True, text=True, timeout=timeout)


def devices() -> list[str]:
    try:
        r = adb("devices", timeout=10)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    out = []
    for line in (r.stdout or "").splitlines():
        if "\tdevice" not in line:
            continue
        s = line.split()[0]
        if s == GEN1_SERIAL:
            continue
        out.append(s)
    return out


def listening(s: str, port: str = "8081") -> bool:
    r = adb(
        "-s",
        s,
        "shell",
        f"netstat -lnt 2>/dev/null | grep {port} || ss -lnt | grep {port}",
        timeout=8,
    )
    return port in (r.stdout or "")


def start_service(s: str) -> None:
    log(f"{s} start camevision-single.sh")
    adb(
        "-s",
        s,
        "shell",
        "chmod 755 /userdata/camevision-single.sh /userdata/camevision-aiq.sh /userdata/S10mira220 2>/dev/null; "
        "if [ -f /userdata/camevision-am.on ]; then "
        "sh /userdata/S10mira220 >/userdata/mira220-boot.log 2>&1; "
        "else "
        "if ! ps | grep -q '[r]kaiq_3A_server'; then "
        "sh /userdata/camevision-aiq.sh >/userdata/aiq-boot.log 2>&1; fi; "
        "fi; "
        "/userdata/camevision-single.sh >/userdata/single-live-boot.log 2>&1",
        timeout=90,
    )


def forward(s: str) -> None:
    adb("-s", s, "forward", "tcp:8081", "tcp:8081")
    adb("-s", s, "forward", "tcp:8083", "tcp:8083")


def live_present(s: str) -> bool:
    r = adb("-s", s, "shell", "test -f /userdata/single_live.py && echo OK", timeout=8)
    return "OK" in (r.stdout or "")


def wait_live(s: str, seconds: int = 50) -> bool:
    t0 = time.time()
    while time.time() - t0 < seconds:
        if listening(s):
            return True
        time.sleep(1)
    return False


def on_connect(s: str, open_page: bool) -> None:
    try:
        if not live_present(s):
            log(f"{s} overlay missing — deploying once")
            sys.path.insert(0, str(ROOT / "tools"))
            import cv_single_overlay_deploy

            cv_single_overlay_deploy.deploy(s)
        if not listening(s):
            start_service(s)
        if not wait_live(s):
            log(f"{s} :8081 still down after start")
            return
        forward(s)
        log(f"{s} page {PAGE}")
        if open_page:
            webbrowser.open(PAGE)
    except subprocess.TimeoutExpired:
        log(f"{s} adb timeout")
    except Exception as e:
        log(f"{s} {type(e).__name__}: {e}")


def _python() -> str:
    from cv_single_paths import bundled_python

    found = bundled_python()
    return str(found) if found is not None else sys.executable


def install_windows() -> int:
    startup = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    vbs = startup / "CameVision-Single-autostart.vbs"
    cmd = ROOT / "tools" / "cv_single_autostart-hidden.cmd"
    py = _python()
    script = ROOT / "tools" / "cv_single_autostart.py"
    cmd.write_text(
        f'@echo off\nstart "" /min "{py}" "{script}" --daemon\n',
        encoding="ascii",
    )
    vbs.write_text(
        'Set sh = CreateObject("WScript.Shell")\r\n'
        f'sh.Run """{py}"" ""{script}"" --daemon", 0, False\r\n',
        encoding="ascii",
    )
    log(f"installed logon helper {vbs}")
    subprocess.Popen(["wscript.exe", str(vbs)], cwd=str(ROOT), close_fds=True)
    return 0


def install_linux() -> int:
    desktop_dir = Path.home() / ".config" / "autostart"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop = desktop_dir / "camevision-single.desktop"
    py = _python()
    script = ROOT / "tools" / "cv_single_autostart.py"
    desktop.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=CameVision Ego Single Sensor\n"
        f'Exec="{py}" "{script}" --daemon\n'
        "X-GNOME-Autostart-enabled=true\n",
        encoding="utf-8",
    )
    os.chmod(desktop, 0o644)
    log(f"installed desktop autostart {desktop}")
    subprocess.Popen(
        [py, str(script), "--daemon"],
        cwd=str(ROOT),
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return 0


def install() -> int:
    if sys.platform == "win32":
        rc = install_windows()
    else:
        rc = install_linux()
    log("USB stays ADB. Plug the board and the page opens by itself.")
    return rc


def already_running() -> bool:
    if not PIDF.is_file():
        return False
    try:
        pid = int(PIDF.read_text(encoding="ascii").strip())
    except ValueError:
        return False
    if pid == os.getpid():
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def daemon() -> int:
    if already_running() and os.getpid() != int(PIDF.read_text(encoding="ascii").strip() or "0"):
        log(f"already running pid={PIDF.read_text(encoding='ascii').strip()}")
        return 0
    PIDF.parent.mkdir(parents=True, exist_ok=True)
    PIDF.write_text(str(os.getpid()), encoding="ascii")
    log("watching for Single ADB")
    armed: set[str] = set()
    while True:
        now = set(devices())
        for s in now - armed:
            log(f"{s} connected")
            on_connect(s, open_page=True)
            armed.add(s)
        for s in now & armed:
            try:
                forward(s)
                if not listening(s):
                    log(f"{s} :8081 dropped, restarting")
                    start_service(s)
                    forward(s)
            except Exception as e:
                log(f"{s} keep {e}")
        for s in armed - now:
            log(f"{s} disconnected")
        armed &= now
        time.sleep(2)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--install", action="store_true", help="install logon / desktop autostart")
    p.add_argument("--daemon", action="store_true", help="run the USB watcher loop")
    p.add_argument("--once", action="store_true", help="deploy/forward once and exit")
    args = p.parse_args()
    if args.install:
        return install()
    if args.once:
        found = devices()
        if not found:
            raise SystemExit("no ADB")
        for s in found:
            on_connect(s, open_page=True)
        return 0
    return daemon()


if __name__ == "__main__":
    raise SystemExit(main())
