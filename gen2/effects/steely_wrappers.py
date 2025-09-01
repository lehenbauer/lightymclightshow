
# gen2/effects/steely_wrappers.py
# Wiring for Steely Glint demos -> callable wrappers consumable by a root daemon.
from __future__ import annotations
from typing import Callable, Dict, Any

# Import concrete effects and logical strips from your codebase
from gen2.dispatcher import LighthouseSweep, NewtonsCradle, BowWave  # type: ignore
from gen2.dispatcher import ForegroundEffect, BackgroundEffect        # type: ignore
from gen2.steely_logical import starboard_strip, port_strip, circular_strip  # type: ignore

REGISTRY: Dict[str, Callable[..., Any]] = {}

def effect(name: str):
    def deco(fn: Callable[..., Any]):
        REGISTRY[name] = fn
        return fn
    return deco

_STRIP_MAP = {
    "starboard": starboard_strip,
    "port":      port_strip,
    "circular":  circular_strip,
}
def _resolve_strip(strip: str):
    s = _STRIP_MAP.get(strip.lower())
    if s is None:
        raise ValueError(f"Unknown strip '{strip}'. Expected one of: {', '.join(_STRIP_MAP)}")
    return s

@effect("lighthouse")
def lighthouse(d, *, strip: str = "circular",
               rotation_speed: float = 0.5,
               beam_width_pct: float = 5.0,
               beam_color_h: float = 0.15,
               beam_intensity: float = 1.0,
               has_fog: bool = True,
               duration: float | None = None) -> ForegroundEffect:
    s = _resolve_strip(strip)
    eff = LighthouseSweep(s).start(rotation_speed=rotation_speed,
                                   beam_width_pct=beam_width_pct,
                                   beam_color_h=beam_color_h,
                                   beam_intensity=beam_intensity,
                                   has_fog=has_fog,
                                   duration=duration)
    d.run_foreground_effect(eff)
    return eff

@effect("newtons_cradle")
def newtons_cradle(d, *, strip: str,
                   num_balls: int = 5,
                   ball_width_pct: float = 2.0,
                   h: float = 0.6, s: float = 0.8, v: float = 1.0,
                   swing_duration: float = 1.0,
                   duration: float | None = None) -> ForegroundEffect:
    sstrip = _resolve_strip(strip)
    eff = NewtonsCradle(sstrip).start(num_balls=num_balls,
                                      ball_width_pct=ball_width_pct,
                                      h=h, s=s, v=v,
                                      swing_duration=swing_duration,
                                      duration=duration)
    d.run_foreground_effect(eff)
    return eff

@effect("bow_wave")
def bow_wave(d, *, strip: str,
             max_speed_knots: float = 18.0,
             bow_position: float = 0.15,
             duration: float | None = None) -> BackgroundEffect:
    sstrip = _resolve_strip(strip)
    eff = BowWave(sstrip).start(max_speed_knots=max_speed_knots,
                                bow_position=bow_position,
                                duration=duration)
    d.run_background_effect(eff)
    return eff

# --- Demo-equivalent wrappers mirroring the CLI scripts ---

@effect("demo.steely.lighthouse")
def demo_steely_lighthouse(d):
    # Create first beam immediately
    eff1 = lighthouse(d,
        strip="circular",
        rotation_speed=0.5,
        beam_width_pct=5.0,
        beam_color_h=0.15,
        beam_intensity=1.0,
        has_fog=True,
        duration=30.0
    )

    # Schedule second beam for 2 seconds later
    # Note: This scheduled effect won't be tracked by the daemon
    d.schedule(2.0, lambda: lighthouse(d,
        strip="circular",
        rotation_speed=-0.3,
        beam_width_pct=3.0,
        beam_color_h=0.0,   # red second beam
        beam_intensity=0.5,
        has_fog=False,
        duration=28.0
    ))

    # Return the first effect so it can be tracked
    return eff1

@effect("demo.steely.newtons_cradle")
def demo_steely_newtons_cradle(d):
    # Create effects immediately instead of scheduling them
    effects = []
    for strip in ("starboard", "port"):
        eff = newtons_cradle(d,
            strip=strip,
            num_balls=5,
            ball_width_pct=2.0,
            h=0.6, s=0.8, v=1.0,
            swing_duration=1.0,
            duration=20.0
        )
        effects.append(eff)
    return effects

@effect("demo.steely.bow_wave")
def demo_steely_bow_wave(d):
    # Create effects immediately instead of scheduling them
    effects = []
    for strip in ("starboard", "port"):
        eff = bow_wave(d,
            strip=strip,
            max_speed_knots=18.0,
            bow_position=0.15,
            duration=30.0  # Set a 30 second duration to prevent infinite running
        )
        effects.append(eff)
    return effects
