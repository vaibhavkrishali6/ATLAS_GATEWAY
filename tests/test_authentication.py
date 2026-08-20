"""Focused integration checks for development JWT authentication."""

from datetime import datetime, timedelta, timezone
import unittest

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from atlas.main import app as atlas_app
from atlas.main_settings import settings as atlas_settings
from services.auth_service.auth import settings as auth_settings
from services.auth_service.main import app as auth_app


class FakeDownstreamClient:
    def __init__(self) -> None:
        self.last_url: str | None = None

    async def request(self, **kwargs: object) -> httpx.Response:
        self.last_url = str(kwargs["url"])
        return httpx.Response(200, content=b"downstream reached")

    async def aclose(self) -> None:
        """Match the shared httpx client's lifespan interface."""


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auth_client = TestClient(auth_app)
        cls.auth_client.__enter__()
        cls.atlas_client = TestClient(atlas_app)
        cls.atlas_client.__enter__()
        cls.downstream = FakeDownstreamClient()
        atlas_app.state.http_client = cls.downstream

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas_client.__exit__(None, None, None)
        cls.auth_client.__exit__(None, None, None)

    def login(self, username: str, password: str) -> str:
        response = self.auth_client.post(
            "/auth/login", json={"username": username, "password": password}
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["access_token"]

    def test_valid_doctor_login_returns_jwt(self) -> None:
        self.assertTrue(self.login("doctor", "doctor123"))

    def test_valid_patient_login_returns_jwt(self) -> None:
        self.assertTrue(self.login("patient", "patient123"))

    def test_invalid_credentials_are_rejected(self) -> None:
        response = self.auth_client.post(
            "/auth/login", json={"username": "doctor", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 401)

    def test_atlas_rejects_missing_or_malformed_token(self) -> None:
        self.assertEqual(self.atlas_client.get("/api/patients").status_code, 401)
        self.assertEqual(
            self.atlas_client.get(
                "/api/patients", headers={"Authorization": "Bearer not-a-jwt"}
            ).status_code,
            401,
        )

    def test_atlas_rejects_expired_or_differently_signed_tokens(self) -> None:
        private_key = auth_settings.auth_private_key_path.read_text(encoding="utf-8")
        expired = jwt.encode(
            {
                "sub": "doctor",
                "role": "doctor",
                "iss": atlas_settings.jwt_issuer,
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            private_key,
            algorithm="RS256",
        )
        self.assertEqual(
            self.atlas_client.get(
                "/api/patients", headers={"Authorization": f"Bearer {expired}"}
            ).status_code,
            401,
        )

        other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        other_token = jwt.encode(
            {
                "sub": "doctor",
                "role": "doctor",
                "iss": atlas_settings.jwt_issuer,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            other_private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ),
            algorithm="RS256",
        )
        self.assertEqual(
            self.atlas_client.get(
                "/api/patients", headers={"Authorization": f"Bearer {other_token}"}
            ).status_code,
            401,
        )

    def test_valid_token_reaches_existing_proxy_route(self) -> None:
        token = self.login("doctor", "doctor123")
        response = self.atlas_client.get(
            "/api/patients", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"downstream reached")
        self.assertEqual(self.downstream.last_url, "http://localhost:8001/patients")


if __name__ == "__main__":
    unittest.main()
