# -------------------------------- gen2/demo_async_lobby.py --------------------------------

from __future__ import annotations
import asyncio
from async_runtime import Engine, Context
from effects_async import slow_wipe, color_wheel, banded_color_wheel
from sinks import TickerSink

async def lobby_show(ctx: Context) -> None:
    ctx._engine.set_order(["bg", "mid", "fg"])  # z-order
    # background: very slow wheel
    await ctx.add(color_wheel(ctx, speed=0.01, duration=120, layer="bg", saturation=0.25, value=0.18))
    # mid: banded traveling slices
    await ctx.add(banded_color_wheel(ctx, periods=5, steps=10, speed=0.03, layer="mid", saturation=0.45, value=0.22, softness=0.12))
    # foreground: occasional wipe accent with opacity pulsing
    async def accent(ctx: Context):
        fg = ctx.layer("fg"); fg.alpha = 0.0
        t0 = ctx.now
        while ctx.now - t0 < 8.0:
            p = (ctx.now - t0) / 8.0
            fg.alpha = 0.6 * (1.0 - abs(2*p - 1.0))
            await ctx.sleep(0)
        fg.alpha = 0.0
    while True:
        await ctx.add(accent(ctx))
        await ctx.sleep(6)

async def _main():
    N = 300  # pixels
    eng = Engine(N, fps=60, frame_sink=TickerSink(every=120))
    await eng.run(lobby_show(Context(eng)))

if __name__ == "__main__":
    asyncio.run(_main())

