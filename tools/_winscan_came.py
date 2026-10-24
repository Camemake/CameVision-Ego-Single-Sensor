"""Find Camemake BLE and print name/UUIDs."""
import asyncio
from bleak import BleakScanner

MAC = "60:48:9C:46:2C:47"


async def main():
    found = {}

    def cb(device, adv):
        name = adv.local_name or device.name or ""
        uuids = list(adv.service_uuids or [])
        found[device.address] = (name, adv.rssi, uuids)
        if device.address.upper() == MAC or "came" in name.lower() or "462C47" in name:
            print("ADV", device.address, "name=%r" % name, "rssi", adv.rssi, "uuids", uuids, flush=True)

    scanner = BleakScanner(cb)
    await scanner.start()
    await asyncio.sleep(10)
    await scanner.stop()
    print("camera", found.get(MAC) or found.get(MAC.lower()) or "MISSING")


if __name__ == "__main__":
    asyncio.run(main())
