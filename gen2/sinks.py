# -------------------------------- gen2/sinks.py --------------------------------

from __future__ import annotations
from typing import Callable
import numpy as np

RGB = np.ndarray  # [N,3] uint8

class TickerSink:
    """Debug sink printing a heartbeat every N frames."""
    def __init__(self, every: int = 120):
        self.i = 0
        self.every = max(1, int(every))
    def __call__(self, frame: RGB) -> None:
        self.i += 1
        if self.i % self.every == 0:
            print(f"frame {self.i}, avg={float(frame.mean()):.1f}")

class CallableSink:
    """Wrap any callable(frame_u8) you already have (e.g., hardware.show)."""
    def __init__(self, fn: Callable[[RGB], None]):
        self.fn = fn
    def __call__(self, frame: RGB) -> None:
        self.fn(frame)

class StdoutDumpSink:
    """For testing: dumps a few pixels to stdout (truncated)."""
    def __init__(self, n_preview: int = 8):
        self.k = n_preview
    def __call__(self, frame: RGB) -> None:
        print(repr(frame[: self.k]))

