from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.limiter import RateLimiter, limiter
from main import app


class RateLimiterUnitTests(unittest.TestCase):
    def test_domain_cooldown_blocks_immediate_rescan(self):
        test_limiter = RateLimiter(domain_cooldown_seconds=60)

        test_limiter.check_domain_cooldown("example.com")

        with self.assertRaises(Exception) as context:
            test_limiter.check_domain_cooldown("example.com")

        self.assertEqual(context.exception.status_code, 429)
        self.assertIn("example.com", context.exception.detail)
        self.assertEqual(context.exception.headers["Retry-After"], "60")

    def test_ip_rate_limit_blocks_eleventh_request_in_window(self):
        test_limiter = RateLimiter(ip_max_requests=10, ip_window_seconds=60)
        client = TestClient(app)

        for _ in range(10):
            test_limiter.check_ip_rate_limit(
                client.build_request("POST", "/api/scan", headers={"X-Forwarded-For": "203.0.113.9"})
            )

        with self.assertRaises(Exception) as context:
            test_limiter.check_ip_rate_limit(
                client.build_request("POST", "/api/scan", headers={"X-Forwarded-For": "203.0.113.9"})
            )

        self.assertEqual(context.exception.status_code, 429)
        self.assertEqual(context.exception.headers["Retry-After"], "60")


class ScanRouteRateLimitingTests(unittest.TestCase):
    def setUp(self):
        limiter.reset()
        self.client = TestClient(app)

    def tearDown(self):
        limiter.reset()

    @patch("app.api.routes.run_scan", new_callable=AsyncMock)
    @patch("app.api.routes.save_scan")
    def test_same_domain_is_put_on_cooldown(self, mock_save_scan, mock_run_scan):
        first = self.client.post("/api/scan", json={"domain": "HTTPS://Example.COM/path"})
        second = self.client.post("/api/scan", json={"domain": "example.com"})

        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.json()["domain"], "example.com")
        self.assertEqual(second.status_code, 429)
        self.assertIn("scanned recently", second.json()["detail"])
        self.assertEqual(second.headers["retry-after"], "60")
        self.assertTrue(mock_save_scan.called)
        self.assertTrue(mock_run_scan.await_count >= 1)

    @patch("app.api.routes.run_scan", new_callable=AsyncMock)
    @patch("app.api.routes.save_scan")
    def test_ip_limit_blocks_eleventh_scan_request(self, mock_save_scan, mock_run_scan):
        headers = {"X-Forwarded-For": "198.51.100.7"}

        for index in range(10):
            response = self.client.post(
                "/api/scan",
                json={"domain": f"example{index}.com"},
                headers=headers,
            )
            self.assertEqual(response.status_code, 202)

        blocked = self.client.post(
            "/api/scan",
            json={"domain": "overflow-example.com"},
            headers=headers,
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Too many scan requests", blocked.json()["detail"])
        self.assertEqual(blocked.headers["retry-after"], "60")
        self.assertEqual(mock_save_scan.call_count, 10)
        self.assertEqual(mock_run_scan.await_count, 10)


if __name__ == "__main__":
    unittest.main()
