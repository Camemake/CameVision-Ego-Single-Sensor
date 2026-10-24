"""Scan Windows BLE advertisements for CameVision / Seekwave."""
import asyncio
import sys
import time

try:
    from bleak import BleakScanner
except ImportError:
    sys.stderr.write("no-bleak\n")
    sys.exit(2)

WANT = ("camevision", "came", "ego", "seekwave", "skw")


async def main():
    found = {}

    def cb(device, adv):
        name = adv.local_name or device.name or ""
        addr = device.address
        rssi = adv.rssi
        key = addr
        found[key] = (name, rssi, adv.manufacturer_data)
        label = name or "?"
        print("ADV %s rssi=%s name=%r" % (addr, rssi, label), flush=True)

    print("scanning 15s...", flush=True)
    scanner = BleakScanner(cb)
    await scanner.start()
    await asyncio.sleep(15)
    await scanner.stop()
    print("=== hits %d ===" % len(found), flush=True)
    hits = 0
    for addr, (name, rssi, mfg) in sorted(found.items(), key=lambda x: x[1][1] or -999, reverse=True):
        low = (name or "").lower()
        mark = " *" if any(w in low for w in WANT) else ""
        if mark:
            hits += 1
        print("%s %s rssi=%s%s" % (addr, name or "(no-name)", rssi, mark))
    print("camevision-like=%d" % hits)


if __name__ == "__main__":
    asyncio.run(main())
