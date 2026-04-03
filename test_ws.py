import asyncio
import websockets

async def test():
    try:
        async with websockets.connect("ws://localhost:8000/ws/feed") as ws:
            print("Connected!")
            await asyncio.sleep(1)
            print("Success")
    except Exception as e:
        print(f"Failed: {repr(e)}")

asyncio.run(test())
