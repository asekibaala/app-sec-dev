import os
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient

os.environ["BUGBOUNTY_HUT_TESTING"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.users import make_local_admin_create
from main import app


class FastAPIUsersAuthTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def test_local_admin_create_maps_username_to_framework_email(self):
        user_create = make_local_admin_create("admin", "admin")

        self.assertEqual(user_create.username, "admin")
        self.assertEqual(user_create.email, "admin@bugbounty-hut.example.com")
        self.assertEqual(user_create.password, "admin")

    def test_login_returns_bearer_token_for_default_admin(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        self.assertEqual(response.json()["token_type"], "bearer")

    def test_auth_me_returns_current_user_after_login(self):
        login = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        token = login.json()["access_token"]

        me = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["username"], "admin")


if __name__ == "__main__":
    unittest.main()
