# Product Improvement Plan: Auto Zoom Controller

**Status**: Proposed
**Date**: 2026-10-06
**Related plans**: `docs/plans/modernization_plan.md`, `docs/plans/web_ui_and_autohotspot_plan.md`

---

## 1. Goal and Current Position

Improve the reliability, safety, and field usability of the Auto Zoom Controller while preserving its focus: an affordable, customizable, single-axis lens-zoom controller for timelapse photography.

The current implementation provides a Raspberry Pi GPIO/DRV8825 motor driver, a configurable CLI, dry-run GPIO emulation, and drift-free interval scheduling. The controller is open-loop: it counts commanded motor steps, but does not sense lens position or camera exposure. Raspberry Pi installer verification remains pending in Phase 8 of the modernization plan. The proposed phone UI and hotspot are specified separately in `web_ui_and_autohotspot_plan.md`; they are not implemented yet.

The project's differentiator is adaptability to a particular manual lens and DIY motor mount, rather than turnkey integration. Relevant commercial references include [DJI Focus Pro](https://www.dji.com/focus-pro), an integrated focus/iris/zoom lens-control system, and [edelkrone HeadONE v2](https://edelkrone.com/products/headone), an app-controlled camera pan/tilt motion system with timelapse support. These products provide more integrated hardware and operator tooling, but solve broader or different motion-control needs than a geared lens-zoom controller.

## 2. Priorities

1. Verify the installer and baseline behavior on actual Raspberry Pi hardware.
2. Add position awareness and travel safeguards before unattended use.
3. Make motor timing and schedule overruns visible and predictable.
4. Coordinate lens movement with image capture.
5. Add field controls and service integration after the hardware behavior is safe.

## 3. Roadmap

### Phase A: Raspberry Pi Bring-Up

**Goal**: Confirm that the packaged application and installer work on the target hardware and OS.

- Complete Phase 8 in `modernization_plan.md` over SSH or VS Code Remote-SSH.
- Record Pi model, OS release/codename, architecture, Python version, and selected GPIO driver.
- Run the installer, verify driver import, `auto-zoom --help`, a short dry-run, and the generated `~/bin/auto-zoom` runner.
- Record which supported OS/driver combination was exercised; track other releases separately.

**Exit criteria**: Installation and CLI smoke checks pass on the Pi without live motor movement.

### Phase B: Lens Position and Motion Safety

**Goal**: Prevent unnoticed step loss and reduce the risk of driving the lens into a mechanical stop.

- Define a lens commissioning workflow for start/end positions and usable travel.
- Add configurable software travel limits and reject commands that exceed the calibrated range.
- Evaluate a homing switch or encoder for recovering position after restart and detecting missed steps.
- Define an accessible emergency power/motor-stop procedure and safe GPIO cleanup behavior.
- Add hardware-independent tests for bounds and state handling, then verify the procedure on the Pi with the lens mechanically protected.

**Exit criteria**: Out-of-range moves are rejected; the operator can establish a known starting position; failure and stop paths leave the motor disabled. Do not claim closed-loop position safety unless position feedback is installed and verified.

### Phase C: Motion Timing and Overrun Handling

**Goal**: Ensure requested intervals remain meaningful under different step counts and motor loads.

- Estimate movement duration from step count and pulse delay, and compare it to the requested interval.
- Detect when a movement overruns its next scheduled activation; report and apply an explicit policy (skip, stop, or continue with a warning) instead of silently catching up.
- Measure pulse timing on the Raspberry Pi under load. If Python/Linux scheduling jitter is material, move pulse generation to a hardware-timed GPIO mechanism or a dedicated microcontroller.
- Evaluate acceleration/deceleration ramps to reduce lost steps at starts and stops.

**Exit criteria**: Overruns are deterministic and visible; measured movement and interval behavior meet documented tolerances for the supported hardware setup.

### Phase D: Camera Capture Synchronization

**Goal**: Keep the lens stationary during exposure and make zoom motion repeatable relative to each frame.

- Select a supported integration: camera shutter control, intervalometer trigger input, or a documented external timing contract.
- Define the sequence for exposure, settle time, and motor movement, including behavior when a capture or movement is late.
- Add mocked tests for ordering and error behavior; test a complete short sequence with the target camera before long unattended runs.

**Exit criteria**: Each frame is captured at a defined lens position, no movement occurs during exposure, and timing failures are reported rather than silently desynchronizing the sequence.

### Phase E: Field Operation and Monitoring

**Goal**: Make the controller manageable from a phone and recoverable after a disconnect or restart.

- Implement the existing web UI/API and background-engine proposal from `web_ui_and_autohotspot_plan.md` only after Phases B-D establish safe motor and capture semantics.
- Include status/progress, manual jog with limits, dry-run indication, pause/resume, and emergency stop; retain CLI parity.
- Add a systemd service only after shutdown, restart, and GPIO cleanup behavior are tested.
- Configure hotspot/network access with secure credentials and avoid exposing unauthenticated motor controls to untrusted networks.

**Exit criteria**: A disconnected client does not stop a mission; reconnecting shows current state; stop and restart paths are verified; remote controls are limited to the intended local network and protected appropriately.

## 4. Cross-Cutting Verification

- Keep the current CI gates: lint, format, tests, and supported Python matrix.
- Add tests for every new safety rule and scheduler decision before hardware integration.
- Use dry-run for routine development, but do not treat it as proof of GPIO, motor, camera, or Pi OS behavior.
- Record hardware model, OS/driver versions, lens, motor, power supply, calibration, and observed timing for each Pi acceptance run.
- Do not run unattended or live-lens tests until the relevant phase's safety checks have passed.

## 5. Completion Definition

The controller is ready for dependable field use when position limits and stop behavior have been verified, scheduled motion meets measured timing tolerances, camera exposure is synchronized with lens movement, the target Pi installation is reproducible, and field status/control can recover from client disconnects without losing mission state.
