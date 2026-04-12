import os
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

os.environ["BUGBOUNTY_HUT_TESTING"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.limiter import RateLimiter, limiter
from main import app


def auth_headers(client: TestClient, client_ip: str = "198.51.100.7") -> dict[str, str]:
    """
    Log in through the framework-managed auth endpoint and return headers for
    protected scan-route tests.
    """
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    token = login_response.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Forwarded-For": client_ip,
    }


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
        self.client.__enter__()

    def tearDown(self):
        limiter.reset()
        self.client.__exit__(None, None, None)

    @patch("app.api.routes.run_scan", new_callable=AsyncMock)
    @patch("app.api.routes.save_scan", new_callable=AsyncMock)
    def test_same_domain_is_put_on_cooldown(self, mock_save_scan, mock_run_scan):
        first = self.client.post(
            "/api/scan",
            json={"scan_name": "Primary example scan", "domain": "HTTPS://Example.COM/path"},
            headers=auth_headers(self.client),
        )
        second = self.client.post(
            "/api/scan",
            json={"scan_name": "Second example scan", "domain": "example.com"},
            headers=auth_headers(self.client),
        )

        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.json()["domain"], "example.com")
        self.assertEqual(first.json()["scan_name"], "Primary example scan")
        self.assertEqual(second.status_code, 429)
        self.assertIn("scanned recently", second.json()["detail"])
        self.assertEqual(second.headers["retry-after"], "60")
        self.assertTrue(mock_save_scan.await_count >= 1)
        self.assertTrue(mock_run_scan.await_count >= 1)

    @patch("app.api.routes.run_scan", new_callable=AsyncMock)
    @patch("app.api.routes.save_scan", new_callable=AsyncMock)
    def test_ip_limit_blocks_eleventh_scan_request(self, mock_save_scan, mock_run_scan):
        headers = auth_headers(self.client)

        for index in range(10):
            response = self.client.post(
                "/api/scan",
                json={"scan_name": f"Example scan {index}", "domain": f"example{index}.com"},
                headers=headers,
            )
            self.assertEqual(response.status_code, 202)

        blocked = self.client.post(
            "/api/scan",
            json={"scan_name": "Overflow example scan", "domain": "overflow-example.com"},
            headers=headers,
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Too many scan requests", blocked.json()["detail"])
        self.assertEqual(blocked.headers["retry-after"], "60")
        self.assertEqual(mock_save_scan.await_count, 10)
        self.assertEqual(mock_run_scan.await_count, 10)


if __name__ == "__main__":
    unittest.main()
