
# daemon/lightsd.py
# Root-only daemon that owns the LED hardware and the Dispatcher.
# Talks to unprivileged web/API via a Unix domain socket (length-prefixed JSON).
from __future__ import annotations
import asyncio, json, os, struct, time, heapq, contextlib, signal, argparse
from typing import Any, Dict

from gen2.dispatcher import Dispatcher  # type: ignore
from gen2.effects import REGISTRY       # type: ignore
# Importing steely_logical will initialize physical + logical strips
from gen2 import steely_logical as _steely  # type: ignore

SOCK_PATH = "/run/lightymc.sock"

def _pack(obj: Dict[str, Any]) -> bytes:
    b = json.dumps(obj, separators=(',', ':')).encode()
    return struct.pack(">I", len(b)) + b

async def _read_exact(reader: asyncio.StreamReader, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = await reader.read(n - len(buf))
        if not chunk:
            raise EOFError
        buf += chunk
    return buf

async def _read_msg(reader: asyncio.StreamReader) -> Dict[str, Any]:
    hdr = await _read_exact(reader, 4)
    (length,) = struct.unpack(">I", hdr)
    data = await _read_exact(reader, length)
    return json.loads(data.decode())

class EffectManager:
    def __init__(self, dispatcher: Dispatcher):
        self.d = dispatcher
        self.cmd_q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.subs: set[asyncio.StreamWriter] = set()
        self._next_id = 1
        self._effects: Dict[int, Any] = {}  # id -> effect object

    async def run(self):
        # Mimic Dispatcher.run(), but allow interleaving commands and WS pushes.
        if self.d.start_time is None:
            self.d.start_time = time.time()
        while True:
            # 1) Handle scheduled actions (event_queue is (fire_time, tie_breaker, action))
            virtual_now = time.time() - self.d.start_time
            while self.d.event_queue and self.d.event_queue[0][0] <= virtual_now:
                _, _, action = heapq.heappop(self.d.event_queue)
                try:
                    action()
                except Exception as e:
                    print("Scheduled action error:", e)

            # 2) Drain command queue
            try:
                while True:
                    cmd = self.cmd_q.get_nowait()
                    await self._handle(cmd)
            except asyncio.QueueEmpty:
                pass

            # 3) Run a frame (but don't block the event loop)
            frame_start = time.time()
            self.d.run_frame()
            frame_elapsed = time.time() - frame_start

            # Log if frame took too long (>50ms)
            if frame_elapsed > 0.05:
                print(f"[{time.strftime('%H:%M:%S')}] Warning: Frame took {frame_elapsed:.3f}s")

            # 4) Broadcast ~5Hz status
            if int(virtual_now * 5) != int((virtual_now - (self.d.frame_time)) * 5):
                await self._broadcast({"event": "status", "data": self._status()})

            # Yield control and maintain frame rate asynchronously
            sleep_time = self.d.frame_time - frame_elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(0)

    def _status(self) -> Dict[str, Any]:
        def capture(eff):
            n = getattr(eff, "__class__", type("X",(object,),{})).__name__
            layer = "bg" if eff in self.d.background_effects else "fg"
            eid = None
            for k, v in self._effects.items():
                if v is eff: eid = k; break
            return {"id": eid, "name": n, "layer": layer}
        active = [capture(e) for e in (self.d.background_effects + self.d.foreground_effects)]
        return {
            "fps": getattr(self.d, "fps", None),
            "active": active,
            "events": len(self.d.event_queue),
        }

    async def _broadcast(self, msg: Dict[str, Any]):
        dead = []
        for w in list(self.subs):
            try:
                w.write(_pack(msg)); await w.drain()
            except Exception:
                dead.append(w)
        for w in dead: self.subs.discard(w)

    async def _reply(self, w: asyncio.StreamWriter | None, id: int | None, ok=True, result=None, error=None):
        if not w: return
        w.write(_pack({"id": id, "ok": ok, "result": result, "error": error}))
        await w.drain()

    async def _handle(self, cmd: Dict[str, Any]):
        method = cmd.get("method")
        params = cmd.get("params", {})
        id_ = cmd.get("id")
        w = cmd.get("writer")

        # Log incoming command
        print(f"[{time.strftime('%H:%M:%S')}] Received command: {method} with params: {params}")

        try:
            if method == "subscribe":
                self.subs.add(w)
                print(f"[{time.strftime('%H:%M:%S')}] Client subscribed to status updates")
                await self._reply(w, id_, result={"ok": True}); return

            if method == "list_effects":
                effects = sorted(REGISTRY.keys())
                print(f"[{time.strftime('%H:%M:%S')}] Listing {len(effects)} available effects")
                await self._reply(w, id_, result={"effects": effects}); return

            if method == "start_effect":
                name = params["name"]
                fn = REGISTRY.get(name)
                if not fn:
                    await self._reply(w, id_, ok=False, error=f"unknown effect '{name}'"); return
                eff = fn(self.d, **params.get("params", {}))
                created_ids = []
                # If the wrapper returned effect(s), assign IDs
                if eff is not None and eff != "scheduled":
                    if isinstance(eff, (list, tuple)):
                        for e in eff:
                            eid = self._next_id; self._next_id += 1
                            self._effects[eid] = e
                            created_ids.append(eid)
                    else:
                        eid = self._next_id; self._next_id += 1
                        self._effects[eid] = eff
                        created_ids.append(eid)
                elif eff == "scheduled":
                    # For scheduled effects, we can't track them properly
                    # Log a warning
                    print(f"[{time.strftime('%H:%M:%S')}] Warning: Effect '{name}' uses scheduling - cannot track or stop individual effects")
                print(f"[{time.strftime('%H:%M:%S')}] Started effect '{name}' with IDs: {created_ids}")
                await self._reply(w, id_, result={"effect_ids": created_ids}); return

            if method == "stop_effect":
                eid = int(params["id"])
                eff = self._effects.pop(eid, None)
                if eff is None:
                    await self._reply(w, id_, ok=False, error="unknown id"); return
                # Remove from whichever list it is in
                if eff in self.d.background_effects:
                    self.d.stop_background_effect(eff)
                if eff in self.d.foreground_effects:
                    self.d.stop_foreground_effect(eff)
                await self._reply(w, id_, result=True); return

            if method == "stop_all":
                # clear both lists in place
                bg_count = len(self.d.background_effects)
                fg_count = len(self.d.foreground_effects)
                for eff in list(self.d.background_effects):
                    self.d.stop_background_effect(eff)
                for eff in list(self.d.foreground_effects):
                    self.d.stop_foreground_effect(eff)
                self._effects.clear()
                # Also clear pending events
                event_count = len(self.d.event_queue)
                self.d.event_queue.clear()
                print(f"[{time.strftime('%H:%M:%S')}] Stopped all effects ({bg_count} bg, {fg_count} fg) and cleared {event_count} events")
                await self._reply(w, id_, result=True); return

            if method == "blackout":
                # Stop all effects and blackout all strips
                bg_count = len(self.d.background_effects)
                fg_count = len(self.d.foreground_effects)
                for eff in list(self.d.background_effects):
                    self.d.stop_background_effect(eff)
                for eff in list(self.d.foreground_effects):
                    self.d.stop_foreground_effect(eff)
                self._effects.clear()
                self.d.event_queue.clear()
                # Blackout all available strips
                from gen2 import steely_logical
                print(f"[{time.strftime('%H:%M:%S')}] Blackout: stopping {bg_count} bg, {fg_count} fg effects and turning off all strips")
                for strip in [steely_logical.starboard_strip, steely_logical.port_strip, steely_logical.circular_strip]:
                    strip.blackout()
                print(f"[{time.strftime('%H:%M:%S')}] Blackout complete")
                await self._reply(w, id_, result=True); return

            print(f"[{time.strftime('%H:%M:%S')}] Unknown method: {method}")
            await self._reply(w, id_, ok=False, error="unknown method")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error handling command {method}: {e}")
            await self._reply(w, id_, ok=False, error=str(e))

async def _client_task(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, mgr: EffectManager):
    print(f"[{time.strftime('%H:%M:%S')}] New client connected")
    try:
        while True:
            msg = await _read_msg(reader)
            msg["writer"] = writer
            await mgr.cmd_q.put(msg)
    except EOFError:
        print(f"[{time.strftime('%H:%M:%S')}] Client disconnected")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Client error: {e}")
    finally:
        with contextlib.suppress(Exception):
            writer.close(); await writer.wait_closed()

async def start_unix_server(manager, socket_path):
    import os
    if os.path.exists(socket_path):
        os.unlink(socket_path)
    server = await asyncio.start_unix_server(lambda r, w: _client_task(r, w, manager), path=socket_path)
    os.chmod(socket_path, 0o666)
    return server

async def start_tcp_server(manager, host, port):
    return await asyncio.start_server(lambda r, w: _client_task(r, w, manager), host=host, port=port)

async def main(socket_path, tcp, verbose=False):
    # Initialize dispatcher and manager
    dispatcher = Dispatcher()
    mgr = EffectManager(dispatcher)

    servers = []
    if socket_path:
        servers.append(await start_unix_server(mgr, socket_path))
        if verbose: print(f"UDS listening on {socket_path}")
    if tcp:
        host, port = tcp.rsplit(":", 1)
        servers.append(await start_tcp_server(mgr, host, int(port)))
        if verbose: print(f"TCP listening on {host}:{port}")
    async with asyncio.TaskGroup() as tg:
        for s in servers:
            tg.create_task(s.serve_forever())
        tg.create_task(mgr.run())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--socket", default=SOCK_PATH)
    ap.add_argument("--tcp", default=None)          # e.g. "127.0.0.1:8765"
    ap.add_argument("--verbose", action="store_true")

    args = ap.parse_args()
    asyncio.run(main(args.socket, args.tcp, args.verbose))
