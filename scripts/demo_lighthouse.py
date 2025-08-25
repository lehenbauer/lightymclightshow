# scripts/steelydemo_lighthouse.py
import asyncio, sys
from lightymclightshow.client.lights_client import LightsClient

async def main():
    lc = LightsClient()
    await lc.run_preset("steely/lighthouse")
    # optionally sleep N seconds, then stop_all:
    await asyncio.sleep(30)
    await lc.stop_all()

if __name__ == "__main__":
    asyncio.run(main())

