#!/usr/bin/env python3
"""Apply SHARE NV + BLE name as soon as the board is reachable."""
import concurrent.futures
import socket
import subprocess
import sys
import time
from pathlib import Path

HOST = "192.168.1.72"
TELNET = 2323
HTTP = "http://192.168.1.44:18765"
HERE = Path(__file__).resolve().parent
NAME = "CameVision Ego Single Sensor"

sys.path.insert(0, str(HERE))
try:
    import cv_tn
except Exception:
    cv_tn = None


def tcp_open(ip: str, port: int, timeout: float = 1.5) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def telnet_up() -> bool:
    global HOST
    if tcp_open(HOST, TELNET):
        return True
    ips = [f"192.168.1.{i}" for i in range(1, 255) if i != 44]
    with concurrent.futures.ThreadPoolExecutor(64) as ex:
        futs = {ex.submit(tcp_open, ip, TELNET, 0.25): ip for ip in ips}
        for fut in concurrent.futures.as_completed(futs):
            if fut.result():
                HOST = futs[fut]
                if cv_tn is not None:
                    cv_tn.HOST = HOST
                print(f"found telnet {HOST}", flush=True)
                return True
    return False


def adb_serial() -> str | None:
    try:
        out = subprocess.check_output(["adb", "devices", "-l"], text=True, timeout=8)
    except Exception:
        return None
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2 or parts[1] != "device":
            continue
        serial = parts[0]
        low = line.lower()
        if serial.startswith("emulator-") or "oneplus" in low:
            continue
        if (
            "cv-ego" in low
            or serial.upper().startswith("CV-EGO")
            or serial.upper() == "E4FECA993701B30C"
        ):
            return serial
    return None


def tn(cmd: str, wait: float = 8.0) -> str:
    if cv_tn is None:
        raise RuntimeError("cv_tn missing")
    return cv_tn.run(cmd, wait)


def adb_write(serial: str, remote: str, text: str) -> None:
    p = subprocess.run(
        ["adb", "-s", serial, "shell", f"cat > {remote}"],
        input=text.encode(),
        timeout=20,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "replace"))


def adb_sh(serial: str, cmd: str, timeout: float = 40.0) -> str:
    p = subprocess.run(
        ["adb", "-s", serial, "shell", cmd],
        timeout=timeout,
        capture_output=True,
    )
    return (p.stdout + p.stderr).decode("utf-8", "replace")


def apply_telnet() -> str:
    out = tn(
        f"wget -q -O /tmp/_recover.sh {HTTP}/_recover.sh && chmod +x /tmp/_recover.sh && sh /tmp/_recover.sh",
        wait=16,
    )
    if "RECOVER_DONE" not in out:
        script = (HERE / "_recover.sh").read_text(encoding="utf-8")
        b64 = subprocess.check_output(
            ["python", "-c", "import base64,sys; print(base64.b64encode(sys.stdin.buffer.read()).decode())"],
            input=script.encode(),
        ).decode().strip()
        out += "\n" + tn(
            f"echo {b64} | base64 -d > /tmp/_recover.sh && chmod +x /tmp/_recover.sh && sh /tmp/_recover.sh",
            wait=16,
        )
    out += "\n" + tn(
        f"wget -q -O /userdata/camevision-wifi.sh {HTTP}/camevision-wifi.sh; "
        f"wget -q -O /userdata/camevision-single.sh {HTTP}/camevision-single.sh; "
        "chmod +x /userdata/camevision-wifi.sh /userdata/camevision-single.sh; echo SCRIPTS_OK",
        wait=8,
    )
    return out


def apply_adb(serial: str) -> str:
    adb_write(serial, "/tmp/_recover.sh", (HERE / "_recover.sh").read_text(encoding="utf-8"))
    adb_write(serial, "/userdata/camevision-wifi.sh", (HERE / "camevision-wifi.sh").read_text(encoding="utf-8"))
    adb_write(serial, "/userdata/camevision-single.sh", (HERE / "camevision-single.sh").read_text(encoding="utf-8"))
    out = adb_sh(serial, "chmod +x /tmp/_recover.sh /userdata/camevision-wifi.sh /userdata/camevision-single.sh; sh /tmp/_recover.sh")
    out += "\n" + adb_sh(serial, "hciconfig -a; echo ===; ip -4 addr show wlan0 | grep inet; echo ===; ps | grep telnetd | grep -v grep")
    return out


def main() -> int:
    print(f"waiting for {HOST}:2323 or adb  (recover+BLE name={NAME})", flush=True)
    deadline = time.time() + 480
    while time.time() < deadline:
        serial = adb_serial()
        if serial:
            print(f"ADB {serial}", flush=True)
            print(apply_adb(serial), flush=True)
            return 0
        if telnet_up():
            print("TELNET up", flush=True)
            print(apply_telnet(), flush=True)
            return 0
        time.sleep(3)
    print("TIMEOUT board still unreachable", flush=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
