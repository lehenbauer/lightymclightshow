# -------------------------------- gen2/perf_harness.py --------------------------------

from __future__ import annotations
import time, math
import numpy as np
from .async_runtime import Engine
from .sinks import TickerSink

# Estimate protocol-limited FPS for WS281x-like @800kHz, 24bpp

def estimate_protocol_fps(pixels: int) -> float:
    t = (pixels * 24) / 800_000.0 + 0.0003  # reset ~300us
    return 1.0 / t

def run_synthetic(num_pixels: int = 600, num_layers: int = 3, seconds: float = 3.0) -> None:
    eng = Engine(num_pixels, fps=120, frame_sink=TickerSink(every=240))
    # Fill layers with moving gradients to exercise compositor
    Ls = [eng.layer(f"L{i}") for i in range(num_layers)]
    x = np.linspace(0.0, 1.0, num_pixels, dtype=np.float32).reshape(-1,1)
    t0 = time.perf_counter(); frames = 0
    end = t0 + seconds
    while time.perf_counter() < end:
        t = time.perf_counter() - t0
        for i, L in enumerate(Ls):
            L.alpha = 0.7
            # moving ramp per channel
            L.buf_lin[:, 0] = np.clip((x[:,0] + 0.3*math.sin(t + i)), 0, 1)
            L.buf_lin[:, 1] = np.clip((x[:,0] + 0.3*math.sin(t*1.2 + i*0.7)), 0, 1)
            L.buf_lin[:, 2] = np.clip((x[:,0] + 0.3*math.sin(t*0.8 + i*1.7)), 0, 1)
        eng._composite_encode()
        frames += 1
    dt = time.perf_counter() - t0
    cpu_fps = frames / dt
    proto_fps = estimate_protocol_fps(num_pixels)
    print(f"Synthetic CPU FPS (composite+encode only): {cpu_fps:.1f} fps")
    print(f"Protocol-limited FPS (one strip @800kHz):  {proto_fps:.1f} fps")
    if cpu_fps > 2*proto_fps:
        print("CPU more than sufficient; protocol likely the bottleneck. Split into parallel lanes if needed.")

if __name__ == "__main__":
    run_synthetic()

