"""Local Flask API and web server for dry-run missions."""

import logging
import platform
import socket
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from waitress import serve

from auto_zoom_controller.DRV8825_Helper import Stepper
from auto_zoom_controller.engine import AutoZoomEngine, MissionConfig
from auto_zoom_controller.logging_config import configure_logging
from auto_zoom_controller.main import DIRECTION_MAP

MIN_INTERVAL_SECONDS = 0.01
MAX_DURATION_MINUTES = 24 * 60
MAX_TOTAL_STEPS = 1_000_000
MAX_ACTIVATIONS = 10_000


def _number(payload, key, default, integer=False):
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    if integer and not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _cpu_temperature_c():
    sensor_path = Path("/sys/class/thermal/thermal_zone0/temp")
    try:
        temperature = float(sensor_path.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None
    if temperature > 1000:
        temperature /= 1000
    return round(temperature, 1)


def create_app(engine=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    mission_engine = engine or AutoZoomEngine()
    app.extensions["auto_zoom_engine"] = mission_engine

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/status")
    def status():
        return jsonify(mission_engine.get_status())

    @app.get("/api/system")
    def system():
        return jsonify(
            hostname=socket.gethostname(),
            platform=platform.system(),
            cpu_temperature_c=_cpu_temperature_c(),
        )

    @app.post("/api/start")
    def start():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="request body must be a JSON object"), 400

        direction_name = payload.get("direction", "in")
        if not isinstance(direction_name, str) or direction_name not in DIRECTION_MAP:
            return jsonify(error="direction must be in, out, backward, or forward"), 400

        try:
            config = MissionConfig(
                number_of_total_turns=_number(payload, "number_of_total_turns", 27200, True),
                interval_in_seconds=_number(payload, "interval_in_seconds", 5.0),
                length_in_minutes=_number(payload, "length_in_minutes", 10.0),
                direction=DIRECTION_MAP[direction_name],
                step_format=Stepper.fullstep,
                dry_run=True,
            )
            if config.interval_in_seconds < MIN_INTERVAL_SECONDS:
                raise ValueError(f"interval_in_seconds must be at least {MIN_INTERVAL_SECONDS}")
            if config.length_in_minutes > MAX_DURATION_MINUTES:
                raise ValueError(f"length_in_minutes cannot exceed {MAX_DURATION_MINUTES}")
            if config.number_of_total_turns > MAX_TOTAL_STEPS:
                raise ValueError(f"number_of_total_turns cannot exceed {MAX_TOTAL_STEPS}")
            activation_count = config.length_in_minutes * 60 / config.interval_in_seconds
            if activation_count < 1:
                raise ValueError("mission must contain at least one activation")
            if activation_count > MAX_ACTIVATIONS:
                raise ValueError(f"mission cannot exceed {MAX_ACTIVATIONS} activations")
            mission_engine.start(config)
        except ValueError as error:
            return jsonify(error=str(error)), 400
        except RuntimeError as error:
            return jsonify(error=str(error)), 409

        return jsonify(mission_engine.get_status()), 202

    @app.post("/api/stop")
    def stop():
        if not mission_engine.stop():
            return jsonify(error="no mission is running"), 409
        return jsonify(mission_engine.get_status()), 202

    @app.post("/api/pause")
    def pause():
        if not mission_engine.pause():
            return jsonify(error="no running mission to pause"), 409
        return jsonify(mission_engine.get_status()), 202

    @app.post("/api/resume")
    def resume():
        if not mission_engine.resume():
            return jsonify(error="no paused mission to resume"), 409
        return jsonify(mission_engine.get_status()), 202

    return app


def main():
    configure_logging()
    logging.getLogger(__name__).info("Serving local dry-run UI at http://127.0.0.1:8080")
    serve(create_app(), host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()
