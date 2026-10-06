"""Tests for the localhost dry-run web interface."""

import threading
import time
import unittest

from auto_zoom_controller.engine import AutoZoomEngine
from auto_zoom_controller.gpio_adapter import mock_gpio, set_dry_run
from auto_zoom_controller.web.server import create_app


class TestWebInterface(unittest.TestCase):
    def setUp(self):
        set_dry_run(True)
        mock_gpio.reset()
        self.engine = AutoZoomEngine()
        self.app = create_app(self.engine)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        if self.engine.get_status()["state"] == "RUNNING":
            self.engine.stop(wait=True)
        mock_gpio.reset()

    def wait_for_state(self, expected_state, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.engine.get_status()
            if status["state"] == expected_state:
                return status
            threading.Event().wait(0.005)
        self.fail(f"engine did not reach {expected_state}: {self.engine.get_status()}")

    def test_homepage_serves_ui_assets(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mission console", response.data)
        self.assertEqual(self.client.get("/static/css/app.css").status_code, 200)
        self.assertEqual(self.client.get("/static/js/app.js").status_code, 200)

    def test_status_starts_idle(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["state"], "IDLE")
        self.assertTrue(response.json["dry_run"])

    def test_new_client_reads_active_mission_status(self):
        response = self.client.post(
            "/api/start",
            json={
                "number_of_total_turns": 0,
                "interval_in_seconds": 5,
                "length_in_minutes": 1,
            },
        )
        self.assertEqual(response.status_code, 202)

        reconnected_client = self.app.test_client()
        status = reconnected_client.get("/api/status")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json["state"], "RUNNING")
        self.assertEqual(status.json["total_activations"], 12)
        self.engine.stop(wait=True)

    def test_start_is_always_dry_run_and_completes(self):
        response = self.client.post(
            "/api/start",
            json={
                "number_of_total_turns": 0,
                "interval_in_seconds": 0.01,
                "length_in_minutes": 0.001,
                "direction": "in",
                "dry_run": False,
            },
        )

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.json["dry_run"])
        status = self.wait_for_state("COMPLETED")
        self.assertEqual(status["activations"], 6)

    def test_start_rejects_invalid_values(self):
        response = self.client.post(
            "/api/start",
            json={"number_of_total_turns": -1},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("negative", response.json["error"])

    def test_start_rejects_non_object_json(self):
        response = self.client.post("/api/start", json=[1, 2, 3])
        self.assertEqual(response.status_code, 400)

    def test_start_rejects_unbounded_dry_run(self):
        response = self.client.post(
            "/api/start",
            json={"interval_in_seconds": 0.001, "length_in_minutes": 10},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("at least", response.json["error"])

    def test_concurrent_start_is_rejected_and_stop_is_accepted(self):
        payload = {
            "number_of_total_turns": 0,
            "interval_in_seconds": 5,
            "length_in_minutes": 1,
        }
        self.assertEqual(self.client.post("/api/start", json=payload).status_code, 202)
        self.assertEqual(self.client.post("/api/start", json=payload).status_code, 409)
        self.assertEqual(self.client.post("/api/stop").status_code, 202)
        status = self.wait_for_state("STOPPED")
        self.assertEqual(status["activations"], 0)


if __name__ == "__main__":
    unittest.main()
