


import asyncio, json, struct

class LightsClient:
    def __init__(self, sock="/run/lightymc.sock"):
        self.sock = sock
        self._id = 0

    async def _conn(self):
        r, w = await asyncio.open_unix_connection(self.sock)
        return r, w

    def _pack(self, obj): 
        b = json.dumps(obj, separators=(",",":")).encode()
        return struct.pack(">I", len(b)) + b

    async def _rpc(self, method, params=None):
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params or {}}
        r, w = await self._conn()
        w.write(self._pack(msg)); await w.drain()
        # read exactly one response
        hdr = await r.readexactly(4)
        (n,) = struct.unpack(">I", hdr)
        data = await r.readexactly(n)
        w.close(); await w.wait_closed()
        resp = json.loads(data)
        if not resp.get("ok", False):
            raise RuntimeError(resp.get("error","RPC error"))
        return resp.get("result")

    # Convenience
    async def list_effects(self): return await self._rpc("list_effects")
    async def start(self, name, layer="fg", params=None): 
        return await self._rpc("start_effect", {"name": name, "layer": layer, "params": params or {}})
    async def stop(self, eid): return await self._rpc("stop_effect", {"id": eid})
    async def stop_all(self): return await self._rpc("stop_all")
    async def set_brightness(self, value: float): return await self._rpc("set_brightness", {"value": value})
    async def run_preset(self, name, params=None): return await self._rpc("run_preset", {"name": name, "params": params or {}})

