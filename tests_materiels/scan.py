import asyncio
from bleak import BleakScanner

async def run():
    devices = await BleakScanner.discover(timeout=5.0)
    for d in devices:
        print(f"{d.address} - {d.name}")

if __name__ == "__main__":
    asyncio.run(run())
