from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.security.auth import (
    create_access_token,
    hash_password,
    verify_access_token,
    verify_password,
)


class PasswordHashingTests(unittest.TestCase):
    def test_hash_password_creates_non_plaintext_value(self):
        stored_hash = hash_password("admin")

        self.assertNotEqual(stored_hash, "admin")
        self.assertTrue(stored_hash.startswith("pbkdf2_sha256$"))

    def test_verify_password_accepts_correct_password(self):
        stored_hash = hash_password("admin")
        self.assertTrue(verify_password("admin", stored_hash))

    def test_verify_password_rejects_incorrect_password(self):
        stored_hash = hash_password("admin")
        self.assertFalse(verify_password("wrong-password", stored_hash))


class AccessTokenTests(unittest.TestCase):
    def test_access_token_round_trip_returns_username(self):
        token = create_access_token("admin")
        self.assertEqual(verify_access_token(token), "admin")


if __name__ == "__main__":
    unittest.main()
