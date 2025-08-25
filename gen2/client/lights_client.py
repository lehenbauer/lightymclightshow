
# client/lights_client.py
import asyncio, json, struct

class LightsClient:
    def __init__(self, sock="/run/lightymc.sock"):
        self.sock = sock
        self._id = 0

    async def _open(self):
        return await asyncio.open_unix_connection(self.sock)

    def _pack(self, obj):
        b = json.dumps(obj, separators=(",",":")).encode()
        return struct.pack(">I", len(b)) + b

    async def _rpc(self, method, params=None):
        self._id += 1
        r, w = await self._open()
        w.write(self._pack({"id": self._id, "method": method, "params": params or {}}))
        await w.drain()
        hdr = await r.readexactly(4)
        (n,) = struct.unpack(">I", hdr)
        data = await r.readexactly(n)
        w.close(); await w.wait_closed()
        resp = json.loads(data.decode())
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error"))
        return resp.get("result")

    async def list_effects(self): return await self._rpc("list_effects")
    async def start(self, name, **params): return await self._rpc("start_effect", {"name": name, "params": params})
    async def stop(self, id): return await self._rpc("stop_effect", {"id": id})
    async def stop_all(self): return await self._rpc("stop_all")
