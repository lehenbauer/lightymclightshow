# -------------------------------- gen2/async_runtime.py --------------------------------

from __future__ import annotations
import asyncio, time
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, List
import numpy as np
from gamma_lut import decode_srgb, encode_srgb

RGBu8 = np.ndarray  # [N,3] uint8
RGBf = np.ndarray   # [N,3] float32 (linear)
FrameSink = Callable[[RGBu8], None]

@dataclass
class Layer:
    name: str
    buf_lin: RGBf       # linear float32 0..1, premultiplied when alpha < 1
    alpha: float = 1.0  # scalar layer alpha 0..1 (premultiplied semantics)
    enabled: bool = True

class Context:
    def __init__(self, engine: "Engine"):
        self._engine = engine
    @property
    def now(self) -> float:
        return self._engine.now
    async def sleep(self, dt: float) -> None:
        await asyncio.sleep(max(0.0, dt))
    async def until(self, t_abs: float) -> None:
        await self.sleep(t_abs - self.now)
    def layer(self, name: str) -> Layer:
        return self._engine.layer(name)
    def add(self, effect_coro: Awaitable[None]) -> asyncio.Task:
        return self._engine.add(effect_coro)

class Engine:
    def __init__(self, num_pixels: int, *, fps: float = 60.0, frame_sink: FrameSink):
        self.N = int(num_pixels)
        self.fps = float(fps)
        self.frame_sink = frame_sink
        self._layers: Dict[str, Layer] = {}
        self._z: List[str] = []
        self._tasks: List[asyncio.Task] = []
        self._t0 = time.monotonic()
        self._stop = False
        # scratch buffers
        self._out_lin: RGBf = np.zeros((self.N, 3), dtype=np.float32)
        self._out_u8: RGBu8 = np.zeros((self.N, 3), dtype=np.uint8)

    @property
    def now(self) -> float:
        return time.monotonic() - self._t0

    def layer(self, name: str) -> Layer:
        if name not in self._layers:
            buf = np.zeros((self.N, 3), dtype=np.float32)
            self._layers[name] = Layer(name=name, buf_lin=buf, alpha=1.0, enabled=True)
            self._z.append(name)
        return self._layers[name]

    def set_order(self, names_back_to_front: List[str]) -> None:
        for n in names_back_to_front:
            self.layer(n)
        self._z = list(names_back_to_front)

    def add(self, effect_coro: Awaitable[None]) -> asyncio.Task:
        task = asyncio.create_task(effect_coro)
        self._tasks.append(task)
        task.add_done_callback(lambda t: self._tasks.remove(t) if t in self._tasks else None)
        return task

    async def run(self, main_coro: Awaitable[None]) -> None:
        ctx = Context(self)
        main_task = asyncio.create_task(main_coro)
        target_dt = 1.0 / self.fps if self.fps > 1e-6 else 0.0
        try:
            while not self._stop:
                t_loop = time.monotonic()
                await asyncio.sleep(0)
                frame_u8 = self._composite_encode()
                self.frame_sink(frame_u8)
                if main_task.done() and not self._tasks:
                    break
                if target_dt:
                    elapsed = time.monotonic() - t_loop
                    left = target_dt - elapsed
                    if left > 0:
                        await asyncio.sleep(left)
        finally:
            for t in list(self._tasks):
                t.cancel()
            main_task.cancel()

    def stop(self):
        self._stop = True

    def _composite_encode(self) -> RGBu8:
        # out_lin is the accumulation buffer in linear space
        out = self._out_lin
        out.fill(0.0)
        for name in self._z:
            L = self._layers[name]
            if not L.enabled:
                continue
            a = np.float32(max(0.0, min(1.0, L.alpha)))
            if a <= 0.0:
                continue
            if a < 1.0:
                # premultiplied over: out = L + (1-a)*out
                out *= (1.0 - a)
                out += L.buf_lin * a
            else:
                # a == 1: max() is often desired; give you both, default to over
                # Over semantics:
                out[...] = L.buf_lin  # full cover; change to max if you prefer policy
                # To use MAX blend instead, comment above and uncomment:
                # np.maximum(out, L.buf_lin, out)
        # encode once at the end
        self._out_u8[...] = encode_srgb(out)
        return self._out_u8

