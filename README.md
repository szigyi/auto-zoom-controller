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
Log in to your Raspberry Pi terminal and install the required system libraries:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

> **Note for Raspberry Pi OS Bookworm (Debian 12):**
> On Bookworm, the GPIO driver has transitioned. If `RPi.GPIO` fails to compile or run, install `rpi-lgpio`:
> ```bash
> pip install rpi-lgpio
> ```

### 2. Clone & Install
Clone the repository onto the Raspberry Pi (typically into `~/dev/`):

```bash
mkdir -p ~/dev && cd ~/dev
git clone https://github.com/szigyi/auto-zoom-controller.git
cd auto-zoom-controller

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the project and its dependencies (schedule, RPi.GPIO)
pip install -e .
pip install RPi.GPIO
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
source venv/bin/activate

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
Parameters in `src/auto_zoom_controller/main.py`:

- **`interval_in_seconds`** (e.g., `2` or `5`): How often the motor advances. Should match your camera's intervalometer interval (e.g., if taking a photo every 5 seconds, set to 5).
- **`length_in_minutes`** (e.g., `60`): Total duration of your timelapse shoot in minutes.
- **`number_of_total_turns`** (e.g., `4000`): Total motor steps required to zoom your lens across its desired range.
  - In full-step mode with a 1.8° stepper motor, 1 full motor revolution = 200 steps.
  - If your gear ratio or belt pulley requires 20 motor rotations to cover the lens throw: $20 \times 200 = 4000\text{ steps}$.

### Calibrating Lens Zoom Throw
1. Move the lens zoom ring manually to the starting position (e.g., 24mm wide).
2. Measure how many motor steps are required to reach the target position (e.g., 70mm telephoto).
3. Update `number_of_total_turns` in [main.py](src/auto_zoom_controller/main.py).

### Running the Script
```bash
cd ~/dev/auto-zoom-controller
python3 -m auto_zoom_controller.main
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
