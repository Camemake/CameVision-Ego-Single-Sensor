"""Watch for the CameVision board BLE address and print its names."""
import asyncio
from bleak import BleakScanner

MAC = "60:48:9C:46:2C:47"
hits = []


def cb(device, adv):
    if device.address.upper() != MAC:
        return
    name = adv.local_name or device.name
    hits.append((name, adv.rssi, adv.service_uuids, list(adv.manufacturer_data.keys())))
    print("CV %s rssi=%s name=%r uuids=%s mfg=%s" % (
        device.address, adv.rssi, name, adv.service_uuids, list(adv.manufacturer_data.keys())
    ), flush=True)


async def main():
    print("watching %s for 12s..." % MAC, flush=True)
    scanner = BleakScanner(cb)
    await scanner.start()
    await asyncio.sleep(12)
    await scanner.stop()
    names = sorted({h[0] for h in hits if h[0]})
    print("packets=%d names=%s" % (len(hits), names))


if __name__ == "__main__":
    asyncio.run(main())
