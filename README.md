# Auto Zoom Controller

Automated lens zoom controller for timelapse photography using a Raspberry Pi, a Waveshare Stepper Motor HAT (DRV8825), and a bipolar stepper motor.

---

## Table of Contents
- [Hardware & Electronics](#hardware--electronics)
  - [Bill of Materials](#bill-of-materials)
  - [Pinout & Connections](#pinout--connections)
  - [Wiring Diagram & Assembly](#wiring-diagram--assembly)
  - [DIP Switches & Microstepping](#dip-switches--microstepping)
  - [Power & Current Limit Calibration](#power--current-limit-calibration)
- [Raspberry Pi Setup](#raspberry-pi-setup)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone & Install](#2-clone--install)
- [Development](#development)
- [Local Web UI (Dry Run)](#local-web-ui-dry-run)
- [Testing](#testing)
- [Field Operation & Smartphone Control](#field-operation--smartphone-control)
  - [1. AutoHotspot Setup (Offline Wi-Fi Access Point)](#1-autohotspot-setup-offline-wi-fi-access-point)
  - [2. Connecting from Your Phone](#2-connecting-from-your-phone)
  - [3. Running via SSH & Tmux (Prevent Interruption)](#3-running-via-ssh--tmux-prevent-interruption)
- [Configuration & Usage](#configuration--usage)
  - [Parameters](#parameters)
  - [Calibrating Lens Zoom Throw](#calibrating-lens-zoom-throw)
  - [Running the Script](#running-the-script)
  - [Quick Motor Test](#quick-motor-test)
- [Version Tags](#version-tags)
- [Troubleshooting](#troubleshooting)

---

## Hardware & Electronics

### Bill of Materials
- **Microcomputer**: Raspberry Pi (Zero W, 3B, 3B+, 4B, etc.) with 40-pin GPIO.
- **Motor Driver HAT**: [Waveshare Stepper Motor HAT (B) / DRV8825](https://www.waveshare.com/wiki/Stepper_Motor_HAT).
- **Motor**: 1.8° Bipolar Stepper Motor (e.g., NEMA 14, NEMA 17, 200 steps per full rotation).
- **Power Supply**: External 8.2V – 28V DC power source (e.g., 9V–12V battery pack or DC adapter) to power the stepper motor through the HAT.
- **Mechanical Rig**: Pulley belt / follow-focus gear ring mounted to your camera lens zoom ring.

### Pinout & Connections
The software controls **Motor Channel 1 (M1)** on the Waveshare HAT with the following BCM GPIO mappings:

| Signal | BCM GPIO | Physical Pin | Description |
|---|---|---|---|
| **ENABLE** | `GPIO 12` | Pin 32 | Motor enable (Active LOW: `0` = ON, `1` = OFF) |
| **DIR** | `GPIO 13` | Pin 33 | Rotation direction (`0` = forward, `1` = backward) |
| **STEP** | `GPIO 19` | Pin 35 | Step clock pulse |
| **MODE0** | `GPIO 16` | Pin 36 | Microstep select bit 0 |
| **MODE1** | `GPIO 17` | Pin 11 | Microstep select bit 1 |
| **MODE2** | `GPIO 20` | Pin 38 | Microstep select bit 2 |

### Wiring Diagram & Assembly

```
+-------------------------------------------------------------+
|                     Raspberry Pi (40-Pin)                   |
+-------------------------------------------------------------+
                              || (Stack HAT on GPIO header)
+-------------------------------------------------------------+
|              Waveshare Stepper Motor HAT (DRV8825)          |
|                                                             |
|  [Power In]               [Motor 1 (M1)]      [DIP Switches]|
|  VIN  GND                  A1  A2  B1  B2       1  2  3  4  |
+---|----|-------------------|---|---|---|--------|--|--|--|--+
    |    |                   |   |   |   |        All OFF (0)
    |    |                   +---+---+---+
    |    |                         |
    |    |              4-wire Bipolar Stepper
    |    |             (Coil A: A1, A2 | Coil B: B1, B2)
    |    |
    |    +---------------- External Power GND (-)
    +--------------------- External Power 9V-12V (+)
```

1. **Mount the HAT**: Place the Waveshare Stepper Motor HAT firmly onto the 40-pin GPIO header of the Raspberry Pi.
2. **Connect the Stepper Motor**:
   - Plug the 4 motor wires into the **M1 screw terminal block** (`A1`, `A2`, `B1`, `B2`).
   - Pairs `A1/A2` form Phase A and `B1/B2` form Phase B. (If the motor vibrates without spinning, swap the positions of one pair, e.g., swap `A1` and `A2`).
3. **Connect External Power**:
   - Wire your 9V–12V external battery pack to the HAT's power terminal block (`VIN` and `GND`).
   - ⚠️ **CAUTION**: Do NOT attempt to power the motor solely from the Raspberry Pi's 5V rail. Always supply external power to the HAT, and observe polarity (`+` to VIN, `-` to GND).

### DIP Switches & Microstepping
- The Waveshare HAT has DIP switches for microstep control.
- Because `AutoZoom.py` uses **software microstep control** (`Stepper.software, Stepper.fullstep`), **set all DIP switches for M1 to `0` (OFF / down)**. This allows the Raspberry Pi GPIOs (`GPIO 16, 17, 20`) to govern microstepping.

### Power & Current Limit Calibration
Before driving the motor under load, adjust the potentiometer next to the DRV8825 chip with a small screwdriver:
- Set $V_{REF} = I_{rated} / 2$ (e.g., for a 1A rated motor, set $V_{REF} \approx 0.5\text{V}$ between the potentiometer wiper and GND).
- Setting this properly prevents the motor and driver from overheating while ensuring sufficient torque to turn the lens ring.

---

## Raspberry Pi Setup

### 1. Prerequisites
Run the installer as your normal Raspberry Pi user with `sudo` access. It installs the required Python, virtual-environment, and Git packages. The one-command installation also requires `curl` and an internet connection:

```bash
sudo apt update
sudo apt install -y curl
```

The installer supports Raspberry Pi OS Bookworm and Bullseye. It selects the GPIO driver for the detected release; do not run the installer with `sudo`, because it creates the virtual environment and command runner in your user account.

### 2. Clone & Install
For a one-command installation, run:

```bash
curl -fsSL https://raw.githubusercontent.com/szigyi/auto-zoom-controller/main/scripts/install_pi.sh | bash
```

The installer clones the project into `~/dev/auto-zoom-controller` if needed, installs it in `.venv`, and creates `~/bin/auto-zoom`. To install from an existing checkout instead:

```bash
cd ~/dev/auto-zoom-controller
./scripts/install_pi.sh
```

If `~/bin` is not on your `PATH`, run the controller as `~/bin/auto-zoom` or add `~/bin` to your shell's `PATH`.

## Development

Create the development environment and install the developer tools with the Makefile:

```bash
make venv
make dev
source .venv/bin/activate
pre-commit
```

## Local Web UI (Dry Run)

Install the optional Flask dependency and start the local mission console from the project virtual environment:

```bash
pip install -e ".[web]"
make web
```

Alternatively, run `auto-zoom-web` directly. Open `http://127.0.0.1:5000` on the same machine; use the numeric IPv4 loopback address rather than `localhost`, which may resolve to a different service. The server binds only to loopback. To view a Pi's local UI from another computer, forward it over SSH to a separate local port:

```bash
ssh -L 127.0.0.1:5001:127.0.0.1:5000 pi@autozoom.local
```

Then open `http://127.0.0.1:5001` on the computer running SSH. The UI runs `AutoZoomEngine` with the same `dry_run=True` setting used by CLI `--dry-run`, which selects `MockGPIO`; it does not invoke the CLI parser or launch a subprocess. This UI cannot move the lens. Real-hardware mode remains unavailable until the safety and Raspberry Pi verification phases are complete.

## Testing

With the virtual environment active, run the test suite with:

```bash
make test
```

Run the lint and test checks together, or run a dry-run motor simulation:

```bash
make check
make run-dry
```

To run tests directly with a terminal coverage report:

```bash
pytest --cov=auto_zoom_controller --cov-report=term
```

---

## Field Operation & Smartphone Control

In the field (with no home Wi-Fi), the Raspberry Pi creates its own standalone Wi-Fi hotspot, allowing you to connect with your phone and control the motor over SSH.

### 1. AutoHotspot Setup (Offline Wi-Fi Access Point)
Install the AutoHotspot installer on the Pi:

```bash
git clone https://github.com/RaspberryConnect/AutoHotspot-Installer.git
cd AutoHotspot-Installer
sudo ./autohotspot-setup.sh
```

**How AutoHotspot works:**
- At boot, the Raspberry Pi searches for known Wi-Fi networks (such as your home router).
- If no known network is found (e.g., outdoors), it automatically spins up an Access Point (e.g., SSID `RPi-Hotspot` or `RaspberryConnect-AP`).
- The Raspberry Pi assigns itself IP: `192.168.50.5` (or `10.42.0.1` depending on configuration).

### 2. Connecting from Your Phone
1. Turn on the Raspberry Pi and wait ~45 seconds for it to boot and launch the hotspot.
2. On your phone, go to **Wi-Fi Settings** and connect to the Pi's hotspot SSID.
3. Open a mobile SSH app:
   - **iOS**: [Termius](https://termius.com/) or [Blink Shell](https://blink.sh/) or [Prompt](https://panic.com/prompt/)
   - **Android**: [Termius](https://termius.com/) or [JuiceSSH](https://juicessh.com/)
4. Connect via SSH:
   ```bash
   ssh pi@192.168.50.5
   ```
   *(Enter your Raspberry Pi password when prompted).*

### 3. Running via SSH & Tmux (Prevent Interruption)
When your phone locks or disconnects, regular SSH sessions terminate, which would stop your timelapse. Always use `tmux` (or `screen`):

```bash
# 1. Start a persistent tmux session
tmux new -s timelapse

# 2. Activate virtual environment and navigate to project
cd ~/dev/auto-zoom-controller
source .venv/bin/activate

# 3. Launch the controller
python3 -m auto_zoom_controller.main

# 4. Detach session (Ctrl+B, then release and press D)
```

You can safely disconnect your phone, let the phone sleep, or walk away. When you reconnect:
```bash
tmux attach -t timelapse
```

---

## Configuration & Usage

### Parameters
Configure the controller through its command-line options:

| Option | Description | Default |
|---|---|---|
| `-i`, `--interval` | Seconds between motor activations | `5.0` |
| `-d`, `--duration` | Total transition duration in minutes | `10.0` |
| `-s`, `--steps` | Total motor steps for the zoom throw | `27200` |
| `--direction` | `in`, `out`, `backward`, or `forward` | `in` |
| `--step-format` | `fullstep`, `halfstep`, `1/4step`, `1/8step`, `1/16step`, or `1/32step` | `fullstep` |
| `--step-delay` | Delay between step pulses in seconds | `0.001` |
| `--dry-run` | Emulate operation without sending GPIO signals | Off |
| `-v`, `--version` | Print the installed package version | |
| `-h`, `--help` | Show all options and exit | |

For example, simulate a short 20-step movement, or run a 10-minute transition on hardware:

```bash
auto-zoom --dry-run --interval 0.5 --duration 0.05 --steps 20
auto-zoom --interval 5 --duration 10 --steps 27200 --direction in
```

### Calibrating Lens Zoom Throw
1. Move the lens zoom ring manually to the starting position (e.g., 24mm wide).
2. Measure how many motor steps are required to reach the target position (e.g., 70mm telephoto).
3. Set the measured step count with the `--steps` option.

### Running the Script
```bash
cd ~/dev/auto-zoom-controller
auto-zoom
```

Output:
```text
Activations:  30.0
Total Turns:  4000
Turns:  133
Control mode: software
forward / backward
turn step: 133
Activated: 1
...
```

### Quick Motor Test
To test motor rotation before mounting onto the camera:
```bash
python3 -c "
import RPi.GPIO as GPIO
from auto_zoom_controller.AutoZoom import AutoZoom
zoom = AutoZoom(turns=200)
zoom.job()
GPIO.cleanup()
"
```

## Version Tags

After merging the release changes to `main` and confirming CI is green, use `scripts/bump_version.sh` to increment the latest stable Git tag. `patch` increments the last number, `minor` increments the middle number and resets patch to zero, and `major` increments the first number and resets the other two. The working tree must be clean when creating a tag.

```bash
# Preview the next patch version without creating a tag
bash scripts/bump_version.sh patch --dry-run

# Create a local minor version tag
bash scripts/bump_version.sh minor

# Create and push a major version tag to start the release workflow
bash scripts/bump_version.sh major --push
```

The script creates an annotated tag locally by default. Use `--push` to push it to `origin`; otherwise, it prints the `git push` command to run when ready. Run `bash scripts/bump_version.sh --help` for usage.

---

## Troubleshooting

- **Motor makes buzzing/vibrating noise but doesn't rotate**:
  - Phase wiring issue: swap `A1` and `A2` wires on the M1 terminal block.
  - Insufficient current: increase current limit slightly via the DRV8825 potentiometer.
  - External power issue: verify external 9V-12V supply is plugged in and switched on.
- **Microstepping is erratic or steps are wrong**:
  - Ensure all M1 DIP switches are turned OFF (`0`).
- **Cannot connect from phone**:
  - Wait at least 60 seconds after boot for AutoHotspot to fail connecting to home Wi-Fi and switch to AP mode.
  - Verify your phone is connected to the Pi hotspot Wi-Fi.
  - Check IP address by running `ip addr` or pinging `192.168.50.5`.
- **Motor turns in wrong direction (zooming out instead of in)**:
  - In [AutoZoom.py](src/auto_zoom_controller/AutoZoom.py#L15), change `Dir=Direction.backward` to `Dir=Direction.forward` (or reverse motor coils `A1`/`A2`).
