# -------------------------------- gen2/gamma_lut.py --------------------------------

from __future__ import annotations
import numpy as np

# Build 256-entry sRGB decode table -> linear float32 in [0,1]
# IEC 61966-2-1 approximation

def build_srgb_to_linear_table() -> np.ndarray:
    x = np.arange(256, dtype=np.float32) / 255.0
    a = 0.055
    lin = np.where(x <= 0.04045, x / 12.92, ((x + a) / (1 + a)) ** 2.4)
    return lin.astype(np.float32)

# Build encode LUT: linear [0,1] -> uint8 sRGB

def build_linear_to_srgb_table() -> np.ndarray:
    # 4096 steps for decent precision; we index by rounding
    n = 4096
    x = np.linspace(0.0, 1.0, n, dtype=np.float32)
    a = 0.055
    srgb = np.where(x <= 0.0031308, x * 12.92, (1 + a) * (x ** (1 / 2.4)) - a)
    out = np.clip(np.round(srgb * 255.0), 0, 255).astype(np.uint8)
    return out

_SRGB2LIN = build_srgb_to_linear_table()
_LIN2SRGB = build_linear_to_srgb_table()

# Optional per-channel calibration curve (identity by default). Supply your own 256-entry LUT per channel.
CAL_R = np.arange(256, dtype=np.uint8)
CAL_G = np.arange(256, dtype=np.uint8)
CAL_B = np.arange(256, dtype=np.uint8)

# Fast decode uint8 RGB -> linear float32

def decode_srgb(buf_u8: np.ndarray) -> np.ndarray:
    # buf_u8: [N,3] uint8
    return _SRGB2LIN[buf_u8]

# Encode linear float32 [N,3] -> uint8 RGB using sRGB then per-channel calibration

def encode_srgb(buf_lin: np.ndarray) -> np.ndarray:
    # clamp & index into LIN2SRGB via scalar mapping
    x = np.clip(buf_lin, 0.0, 1.0)
    # scale to 0..4095 indices
    idx = np.minimum((x * (len(_LIN2SRGB) - 1)).astype(np.int32), len(_LIN2SRGB) - 1)
    sr = _LIN2SRGB[idx[..., 0]]
    sg = _LIN2SRGB[idx[..., 1]]
    sb = _LIN2SRGB[idx[..., 2]]
    # per-channel calibration
    out = np.empty_like(buf_lin, dtype=np.uint8)
    out[..., 0] = CAL_R[sr]
    out[..., 1] = CAL_G[sg]
    out[..., 2] = CAL_B[sb]
    return out

