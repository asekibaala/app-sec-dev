from pathlib import Path
import sys
import unittest

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.validators import ScanRequest, sanitise_domain


class ScanRequestValidatorTests(unittest.TestCase):
    def test_normalises_scheme_path_and_case(self):
        request = ScanRequest(domain="  HTTPS://Example.COM/path?q=1#frag ")
        self.assertEqual(request.domain, "example.com")

    def test_rejects_private_ip(self):
        with self.assertRaises(ValidationError) as context:
            ScanRequest(domain="127.0.0.1")

        self.assertIn("Scanning private or loopback IP addresses is not permitted", str(context.exception))

    def test_rejects_public_ip(self):
        with self.assertRaises(ValidationError) as context:
            ScanRequest(domain="8.8.8.8")

        self.assertIn("Please enter a domain name, not an IP address", str(context.exception))

    def test_rejects_private_hostname(self):
        with self.assertRaises(ValidationError) as context:
            ScanRequest(domain="localhost")

        self.assertIn("private hostname", str(context.exception))

    def test_rejects_invalid_domain_labels(self):
        with self.assertRaises(ValidationError) as context:
            ScanRequest(domain="bad_domain!.com")

        self.assertIn("is not a valid domain name", str(context.exception))

    def test_rejects_missing_tld(self):
        with self.assertRaises(ValidationError) as context:
            ScanRequest(domain="intranet")

        self.assertIn("missing a TLD", str(context.exception))

    def test_sanitise_domain_strips_port(self):
        self.assertEqual(sanitise_domain("https://example.com:8443/test"), "example.com")


if __name__ == "__main__":
    unittest.main()
