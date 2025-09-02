# LightyMcLightShow - System Architecture Overview

## What is LightyMcLightShow?

LightyMcLightShow (LML) is a sophisticated Python-based RGB LED strip control system built on the Raspberry Pi platform. It provides professional-grade lighting effects with features rarely seen in consumer LED controllers, including frame-rate independence, multi-effect layering, environmental responsiveness (GPS, motion sensors), and distributed multi-Pi synchronization capabilities.

## Core Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   lightctl   │  │   Web UI     │  │  Custom App  │  │
│  │   (CLI)      │  │   (Future)   │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    Length-Prefixed JSON
                    over Unix Socket/TCP
                             │
┌─────────────────────────────┼───────────────────────────┐
│                    Daemon Layer (sudo)                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │              lightsd (gen2/daemon/)               │  │
│  │  - Owns hardware access (PWM/SPI)                 │  │
│  │  - Manages effect lifecycle                       │  │
│  │  - Handles client connections                     │  │
│  └─────────────────────┬─────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────┘
                         │
┌────────────────────────┼─────────────────────────────────┐
│                 Core Engine Layer                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Dispatcher (gen2/dispatcher.py)        │   │
│  │  - Frame-rate independent timing                  │   │
│  │  - Background/foreground effect layering          │   │
│  │  - Event scheduling and management                │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Strip Abstractions                   │   │
│  │  - Physical Strip (hardware interface)            │   │
│  │  - Logical Strip (named segments)                 │   │
│  │  - Virtual Strip (simulation/testing)             │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┼─────────────────────────────────┐
│                  Hardware Layer                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │            rpi_ws281x Library                     │   │
│  │  - PWM0/PWM1/PCM/SPI control                      │   │
│  │  - Direct memory access for LED data              │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

## Directory Structure

### `/gen2/` - Current Generation Implementation
The active codebase containing all modern implementations:

- **`daemon/`** - Server daemon that runs with superuser privileges
  - `lightsd.py` - Main daemon process handling hardware access and client connections

- **`effects/`** - Effect registry and wrappers
  - `steely_wrappers.py` - Effect wrapper implementations
  - Effect registry for dynamic effect discovery

- **Core Files:**
  - `dispatcher.py` - Central animation engine with frame timing and effect scheduling
  - `strip.py` - Base strip abstraction
  - `physical_strip.py` - Hardware LED strip interface using rpi_ws281x
  - `logical_strip.py` - Named segment abstractions (e.g., "starboard", "port")
  - `virtual_strip.py` - Software simulation for testing
  - `hardware.py` - Hardware configuration (GPIO pins, strip types)

- **Effect Implementations:**
  - `*_demo.py` files - Various lighting effects (fills, chases, sparkles, etc.)
  - `steely_*.py` files - Advanced effects with environmental awareness
  - `effects_async.py` - Asynchronous effect support

- **Utilities:**
  - `image_stuff.py` - Image-to-LED animation (playing images as "piano rolls")
  - `gamma_lut.py` - Gamma correction lookup tables
  - `async_runtime.py` - Async/await support infrastructure

### `/scripts/` - Command Line Tools
- `lightctl.py` - Primary CLI client for controlling the daemon
  - Commands: `list`, `start`, `stop-all`, `blackout`, `watch`
  - Supports both Unix socket and TCP connections

### `/attic/` and `gen2/attic/` - Legacy Code
Historical implementations kept for reference but not actively used.

## How Components Interact

### 1. **Server Startup**
```bash
sudo -E PYTHONPATH=. lightenv/bin/python -m gen2.daemon.lightsd \
    --socket /tmp/lightymc.sock \
    --tcp 127.0.0.1:8765 \
    --verbose
```
The daemon starts with root privileges (required for hardware access), creates communication endpoints, and initializes the Dispatcher engine.

### 2. **Client Communication**
Clients connect via Unix socket or TCP and send JSON-RPC style commands:
```python
{
    "id": 1,
    "method": "start_effect",
    "params": {
        "name": "demo.steely.bow_wave",
        "params": {"max_speed_knots": 18.0}
    }
}
```

### 3. **Effect Execution**
The daemon receives commands and instructs the Dispatcher to:
- Load the requested effect class
- Initialize it with provided parameters
- Add it to either the background or foreground effect layer
- Step the effect forward each frame based on elapsed time

### 4. **Frame Rendering**
The Dispatcher maintains a consistent frame rate:
1. Steps all background effects (modify base layer)
2. Applies background to physical strip
3. Steps all foreground effects (modify on top)
4. Calls `strip.show()` to push data to LEDs

## Key Design Principles

### Frame-Rate Independence
Effects calculate their state based on elapsed time, not frame count. This means:
- Effects run consistently regardless of hardware speed
- Upgrading from 30fps to 100fps requires no code changes
- Animations remain smooth even under varying system load

### Percentage-Based Positioning
Effects specify positions as percentages of strip length rather than pixel counts:
- A "50% fill" works identically on 150-LED and 600-LED strips
- Installations can change LED density without modifying effects

### Layered Effects System
- **Background Effects**: Modify a base layer (typically one active)
- **Foreground Effects**: Apply on top of background (multiple simultaneous)
- Example: A color wheel background with sparkles and chases in foreground

### Environmental Awareness
Effects can respond to real-world inputs:
- **GPS**: Speed-responsive effects (bow waves that intensify with boat speed)
- **IMU**: Motion-reactive patterns (acceleration, rotation)
- **Audio**: Music-synchronized effects via FFT analysis
- **Time**: Sunrise/sunset aware, scheduled changes

## Effect Types and Examples

### Basic Effects
- **Fill**: Gradual color transitions across the strip
- **Chase**: Moving blocks of color
- **Sparkle**: Random twinkling pixels
- **Pulse**: Brightness oscillation
- **Raindrop**: Falling light droplets

### Advanced Effects
- **Bow Wave**: GPS-speed reactive wave pattern for boats
- **Lighthouse**: Rotating beacon effect
- **Newton's Cradle**: Physics-simulated pendulum lights
- **Image Player**: Display image files as animated sequences

### Effect Parameters
Effects accept configuration parameters for customization:
```python
timeline.bow_wave.start(
    max_speed_knots=18.0,    # Speed for maximum effect
    bow_position=0.15,        # Wave origin at 15% of strip
    duration=None             # Run indefinitely
)
```

## Communication Protocol

### Message Format
- Length-prefixed JSON over Unix socket or TCP
- 4-byte big-endian length header followed by JSON payload
- Supports request/response and event subscriptions

### Available Commands
- `list_effects` - Get available effect names
- `start_effect` - Launch an effect with parameters
- `stop_all` - Stop all running effects
- `blackout` - Stop effects and turn off all LEDs
- `subscribe` - Receive status updates (~5Hz)

## Hardware Configuration

### LED Strip Support
- **WS2812B** and compatible individually-addressable RGB LEDs
- **WS2815** 12V strips for longer runs
- **RGBW** strips with dedicated white channel
- Multiple strips per Pi (using different GPIO pins)

### Control Methods
- **PWM0/PWM1**: Hardware PWM channels (requires root)
- **PCM**: Audio-based timing (conflicts with audio)
- **SPI**: Serial interface (doesn't require root with proper permissions)

### Level Shifting
3.3V Raspberry Pi GPIO signals must be shifted to 5V for LED data:
- Adafruit Pixel Shifter or similar fast level converters
- Critical for signal integrity over long cable runs

## Performance Characteristics

### Update Rates
- ~110 Hz maximum for 300 RGB LEDs
- ~80-85 Hz for 300 RGBW LEDs
- Scales linearly with LED count (600 LEDs ≈ half the frame rate)

### Optimization Features
- Gamma correction lookup tables for perceptual linearity
- Efficient array operations using Python slicing
- Frame timing monitoring with warnings for slow frames

## Future Capabilities

### Multi-Pi Synchronization
Multiple Raspberry Pis can coordinate over network:
- Synchronized effects across large installations
- Distributed control for architectural lighting
- Network time protocol for coordination without direct connection

### Web Interface
Planned browser-based control panel:
- Real-time effect selection and configuration
- Visual strip layout editor
- Effect parameter sliders and color pickers
- Status monitoring dashboard

## Development Workflow

### Creating New Effects
1. Inherit from `BackgroundEffect` or `ForegroundEffect`
2. Implement `init()` for parameter setup
3. Implement `step(elapsed_time)` for animation logic
4. Register in the effects module
5. Test with virtual strip before hardware

### Testing
- Use `VirtualStrip` for development without hardware
- Run effects in demo files for isolated testing
- Monitor daemon logs for timing and performance issues

## System Requirements

### Software Dependencies
- Python 3.x with venv support
- rpi_ws281x library
- Optional: gpsd (GPS support), pyFFTW (audio analysis)

### Hardware Requirements
- Raspberry Pi (any model with GPIO)
- Appropriate power supply for LED count
- Level shifter for 3.3V → 5V conversion
- LED strips (WS281x compatible)

## Security Considerations

The daemon requires root access for hardware control but implements privilege separation:
- Daemon runs as root for `/dev/mem` access
- Clients connect over Unix socket or TCP without privileges
- Socket permissions control access (`lights` group membership)