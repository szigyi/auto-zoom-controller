# Next Steps: Raspberry Pi Bring-Up and Zoom Calibration

**Status**: Pending real Raspberry Pi connection
**Date**: 2026-10-07
**Related plans**: `modernization_plan.md`, `product_improvement_plan.md`, `web_ui_and_autohotspot_plan.md`

---

## Purpose

Use this checklist during a future SSH or VS Code Remote-SSH session to validate the installer and local web service on the actual Raspberry Pi, review the improvement roadmap against the available hardware, and decide how lens zoom limits can be calibrated safely.

## Current Safety Boundaries

- The web UI starts missions with the shared engine's `dry_run=True` setting, equivalent to CLI `--dry-run`; it uses mock GPIO and cannot move the lens.
- The web server binds to `127.0.0.1`. Remote viewing should use an SSH tunnel, not expose the server to a LAN.
- The controller counts commanded steps and has no encoder, homing switch, or other lens-position feedback today.
- Do not treat manually turning the zoom ring as a measurable calibration operation unless position feedback is added.
- Do not run live motor moves, drive into lens stops, change Wi-Fi profiles, or test unattended operation until the relevant safety decision and hardware checks below are complete.

## 1. Connect and Record Hardware

- [ ] Connect to the Pi over SSH or VS Code Remote-SSH as the normal Pi user; do not run the project installer as root.
- [ ] Record the Pi model, Raspberry Pi OS name/version/codename, kernel, architecture, Python version, GPIO HAT/driver, motor model, power supply, camera, lens, and motor-to-ring mounting method.
- [ ] Record which network manager is active (`NetworkManager`/`nmcli`, `wpa_supplicant`, or another service) without changing its configuration.
- [ ] Confirm the checkout contains the intended implementation revision and has no unrelated uncommitted changes before installing.

Useful read-only inventory commands:

```bash
tr -d '\0' < /proc/device-tree/model
cat /etc/os-release
uname -a
uname -m
python3 --version
command -v nmcli || true
```

## 2. Verify Installation

- [ ] Run `./scripts/install_pi.sh` from the checkout as the normal user; record the selected OS branch and GPIO package.
- [ ] Install the optional web dependencies: `.venv/bin/pip install -e ".[web]"`.
- [ ] Verify the GPIO compatibility import without driving pins: `.venv/bin/python -c 'import RPi.GPIO; print(RPi.GPIO.VERSION)'`.
- [ ] Verify `.venv/bin/auto-zoom --help` and a short `.venv/bin/auto-zoom --dry-run --interval 0.5 --duration 0.05 --steps 20`.
- [ ] Confirm dry-run reports mock GPIO and does not energize or move the motor.
- [ ] Record installer output, Python/GPIO package versions, and any warnings or manual fixes.

**Pass condition**: The install and CLI dry-run succeed on the recorded Pi OS/GPIO combination without live motor movement.

## 3. Verify the User Web Service

- [ ] From the checkout, run `make service-install` as the normal Pi user.
- [ ] Check `systemctl --user status autozoom-web.service` and `journalctl --user -u autozoom-web.service -n 100 --no-pager`.
- [ ] Verify the Pi-local page and API return successfully: `curl -I http://127.0.0.1:8080/`, `curl http://127.0.0.1:8080/api/status`, and `curl http://127.0.0.1:8080/api/system`.
- [ ] Open an SSH tunnel from the Mac, replacing the user and host as needed:

```bash
ssh -L 127.0.0.1:8080:127.0.0.1:8080 <pi-user>@<pi-host>
```

- [ ] On the Mac, open `http://127.0.0.1:8080`; verify controller hostname and CPU temperature are displayed when available.
- [ ] Restart the user service, confirm it returns to `IDLE`, and inspect logs for unexpected GPIO or networking errors.
- [ ] Verify login-start behavior. Only enable user lingering after confirming the user service is intended to run at boot: `sudo loginctl enable-linger <pi-user>`.
- [ ] Verify rollback with `make service-uninstall`; confirm the unit is disabled/removed and the port is no longer served.

**Pass condition**: Waitress serves only on Pi loopback, the SSH tunnel works, restart is clean, and uninstall restores the prior service state. Do not expose port 8080 directly to the LAN.

## 4. Exercise the UI Without Moving the Lens

- [ ] In the tunnelled UI, confirm the displayed mode is dry-run and the real motor cannot be selected.
- [ ] Change duration, interval, steps, and direction; compare the preview with `Logic.calculate_number_of_activations` and `Logic.calculate_number_of_turns`.
- [ ] Start a short mission; verify progress increments and the system remains in mock GPIO mode.
- [ ] Pause between activations, wait, and resume; verify elapsed/next-activation timing shifts by the paused duration.
- [ ] Stop a mission during an interval wait; verify the engine reaches `STOPPED` and reports a useful status after page reload/reconnect.
- [ ] Try invalid and over-limit values; confirm the API rejects them without starting a worker.
- [ ] Confirm the UI's displayed system information contains only read-only host/platform/temperature data; temperature may be unavailable on some OS images.

**Pass condition**: UI controls match API state, reconnect returns authoritative state, and all UI operations remain dry-run-only.

## 5. Review the Product Improvement Plan on the Pi

While the real hardware and lens are available, review every phase of `product_improvement_plan.md` against the recorded setup:

- [ ] Confirm the target lens, motor, gearing, current limit, power supply, and mounting can support the proposed motion safely.
- [ ] Decide whether a controlled software step-count calibration is sufficient or whether an encoder, homing switch, or other position sensor is needed.
- [ ] Specifically assess the proposed workflow of setting minimum zoom and recording maximum zoom. With the current open-loop driver, hand-turning the ring cannot be measured; record what sensor or controlled motor-jog procedure would make the endpoints observable.
- [ ] Define a safe end-stop margin, maximum allowed jog, recovery behavior after a power loss, and emergency stop procedure before enabling live jog.
- [ ] Measure one motor activation time and scheduler jitter on the Pi under the actual motor load; update the overrun policy if the configured interval cannot be met.
- [ ] Identify the camera/intervalometer interface and settle time needed to keep the lens stationary during exposure.
- [ ] Reorder or revise `product_improvement_plan.md` based on evidence from the hardware, and record unresolved assumptions rather than marking unverified work complete.

### Calibration Decision

Choose one method before implementing endpoint capture:

1. **Open-loop commanded-step calibration**: Move the motor in small, supervised increments from a manually established minimum position, count commanded steps, and stop short of mechanical lens stops. This estimates position only; missed steps or manual back-driving invalidate the count. Store conservative software limits and require re-homing after uncertain movement.
2. **Position-feedback calibration**: Add an encoder or suitable homing/limit sensors so manually moved or missed-step positions can be observed. Define sensor mounting, resolution, homing direction, failure behavior, and endpoint margin before adding UI controls.

Do not implement a UI action that claims to record a manually rotated lens endpoint until the chosen hardware can actually measure that position.

## 6. Gate for Live Zoom Testing

Live zoom testing is a separate approval gate, not part of installer verification or the dry-run UI test.

- [ ] Complete and document the Phase B safety decisions in `product_improvement_plan.md`.
- [ ] Add and test software travel bounds and stop/error behavior before presenting a live motor option.
- [ ] With power disconnected, inspect motor wiring, HAT seating, lens mount, gear engagement, and clearance through the intended range.
- [ ] Define a supervised test with the lens protected from hard-stop contact, minimal movement first, a reachable power disconnect, and no unattended duration.
- [ ] Reconnect the motor only after the physical setup is verified; test at the lowest safe speed and smallest useful step count, then confirm direction and stop behavior.
- [ ] Calibrate minimum and maximum positions using the selected method and record the lens, direction convention, raw counts, safety margins, and configuration location.
- [ ] Verify that out-of-range requests are rejected, limits survive restart, and an uncertain/restarted position blocks live missions until re-established.
- [ ] Only after these checks pass, decide whether to enable live control in the UI. Keep the default mode dry-run.

**Do not proceed to a long timelapse or test by driving the lens against either hard stop.**

## 7. Hotspot Decision (Separate Pi Network Change)

- [ ] First record the Pi OS version and active network manager; the current installer does not configure Wi-Fi or a hotspot.
- [ ] Decide whether a field hotspot is needed at all; a known home Wi-Fi plus SSH tunnel may be enough for development.
- [ ] If needed, choose the SSID, a strong operator-supplied password, subnet/DHCP range, interface, and fallback trigger with the operator.
- [ ] Design an opt-in configuration and rollback that preserves existing Wi-Fi profiles; do not assume profile priority alone creates a timed fallback.
- [ ] Test client Wi-Fi, fallback AP, phone reachability, service reachability, and recovery to client Wi-Fi on the actual OS image.
- [ ] Record measured boot/fallback time and address; do not publish fixed network claims before these tests pass.

## Session Record

Fill this in during the Pi session:

- Pi model / revision:
- Raspberry Pi OS version / codename:
- Architecture / Python version:
- GPIO driver and version:
- Motor / lens / mount:
- Network manager:
- Installer and service results:
- Dry-run UI results:
- Calibration method selected and why:
- Product improvement plan changes:
- Live zoom test approved? By whom, after which safety checks:
- Remaining blockers / follow-up work:
