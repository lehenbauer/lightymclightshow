# -------------------------------- gen2/effects_async.py --------------------------------

import numpy as np
from async_runtime import Context
from gamma_lut import decode_srgb

# Utility: fill a layer with constant sRGB color quickly (decoding once)

def _const_linear(rgb_u8):
    return decode_srgb(rgb_u8.astype(np.uint8).reshape(1,3))[0]

async def slow_wipe(ctx: Context, *, color: str = "#668a9e", duration: float = 10.0, layer: str = "bg") -> None:
    L = ctx.layer(layer)
    N = L.buf_lin.shape[0]
    rgb = _const_linear(np.array([int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)], dtype=np.uint8))
    t0 = ctx.now; t1 = t0 + max(1e-6, duration)
    while ctx.now < t1:
        p = (ctx.now - t0) / (t1 - t0)
        i = int(p * N)
        if i > 0:
            L.buf_lin[:i, :] = rgb
        if i < N:
            # soft decay on the tail
            L.buf_lin[i:, :] *= 0.9
        await ctx.sleep(0)
    L.buf_lin[...] = rgb

# HSV helpers (vectorized), returning linear RGB via sRGB decode of a uint8 mapping for speed

def _hsv_to_u8(h: np.ndarray, s: float, v: float) -> np.ndarray:
    h = (h % 1.0) * 6.0
    i = np.floor(h).astype(np.int32)
    f = (h - i).astype(np.float32)
    p = np.float32(v * (1.0 - s))
    q = np.float32(v * (1.0 - s * f))
    t = np.float32(v * (1.0 - s * (1.0 - f)))
    choices = np.stack([
        np.stack([v, t, p], axis=-1),
        np.stack([q, v, p], axis=-1),
        np.stack([p, v, t], axis=-1),
        np.stack([p, q, v], axis=-1),
        np.stack([t, p, v], axis=-1),
        np.stack([v, p, q], axis=-1)
    ], axis=0)
    rgb = choices[i, np.arange(h.shape[0])].astype(np.float32)
    u8 = np.clip(np.round(rgb * 255.0), 0, 255).astype(np.uint8)
    return u8

async def color_wheel(ctx: Context, *, speed: float = 0.02, duration: float = 30.0, layer: str = "bg", saturation: float = 0.3, value: float = 0.25) -> None:
    L = ctx.layer(layer)
    N = L.buf_lin.shape[0]
    base = np.linspace(0.0, 1.0, N, endpoint=False)
    t0 = ctx.now; t1 = t0 + duration
    while ctx.now < t1:
        t = ctx.now - t0
        h = (base + speed * t) % 1.0
        u8 = _hsv_to_u8(h, saturation, value)
        L.buf_lin[:, :] = decode_srgb(u8)
        await ctx.sleep(0)

async def banded_color_wheel(ctx: Context, *, periods: int = 4, steps: int = 12, speed: float = 0.03, layer: str = "bg", saturation: float = 0.6, value: float = 0.25, softness: float = 0.0) -> None:
    L = ctx.layer(layer)
    N = L.buf_lin.shape[0]
    x = np.linspace(0.0, 1.0, N, endpoint=False)
    k = float(periods)
    def quantize_hue(h: np.ndarray) -> np.ndarray:
        h_mod = (h % 1.0) * steps
        if softness <= 1e-6:
            q = np.round(h_mod) / steps
            return q % 1.0
        c = np.floor(h_mod) + 0.5
        d = np.abs(h_mod - c)
        w = np.clip(1.0 - d / softness, 0.0, 1.0)
        q_hard = np.round(h_mod) / steps
        q = (w * q_hard + (1 - w) * (h_mod / steps)) % 1.0
        return q
    t0 = ctx.now
    while True:
        t = ctx.now - t0
        hue = k * x + speed * t
        hue_q = quantize_hue(hue)
        u8 = _hsv_to_u8(hue_q, saturation, value)
        L.buf_lin[:, :] = decode_srgb(u8)
        await ctx.sleep(0)

async def run_step_effect(ctx: Context, *, step_fn, max_duration: float | None = None, layer: str = "fg") -> None:
    t0 = ctx.now
    while True:
        done = bool(step_fn(ctx.now))
        if done:
            break
        if max_duration is not None and (ctx.now - t0) >= max_duration:
            break
        await ctx.sleep(0)

