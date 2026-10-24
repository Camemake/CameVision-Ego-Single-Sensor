"""Connect to camera GATT and send hello."""
import asyncio
from bleak import BleakClient

MAC = "60:48:9C:46:2C:47"
CMD = "6c9a0002-1a6f-4e84-8a00-63616d657631"
INFO = "6c9a0003-1a6f-4e84-8a00-63616d657631"


async def main():
    def on_info(_, data):
        print("INFO", data[:80], flush=True)

    print("connecting", MAC, flush=True)
    async with BleakClient(MAC, timeout=25) as client:
        print("connected", client.is_connected, flush=True)
        for s in client.services:
            print("svc", s.uuid, flush=True)
            for c in s.characteristics:
                print("  chr", c.uuid, c.properties, flush=True)
        try:
            await client.start_notify(INFO, on_info)
        except Exception as exc:
            print("notify", exc, flush=True)
        await client.write_gatt_char(CMD, b'{"cmd":"hello"}', response=False)
        await asyncio.sleep(2)
        print("GATT_OK", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
