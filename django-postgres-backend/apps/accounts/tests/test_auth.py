from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.password = "demoPass123"
        self.user = User.objects.create_user(
            username="demo", email="demo@example.com", password=self.password
        )

    def test_login_returns_tokens(self):
        resp = self.client.post(
            "/api/v1/auth/token/", {"username": self.user.username, "password": self.password}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_full_password_reset_flow(self):
        forgot = self.client.post(
            "/api/v1/accounts/forgot-password/",
            {"email": self.user.email},
            format="json",
        )
        self.assertEqual(forgot.status_code, status.HTTP_200_OK)
        uid = forgot.data.get("uid")
        token = forgot.data.get("token")
        self.assertTrue(uid)
        self.assertTrue(token)

        reset = self.client.post(
            "/api/v1/accounts/reset-password/",
            {"uid": uid, "token": token, "new_password": "Newpass123"},
            format="json",
        )
        self.assertEqual(reset.status_code, status.HTTP_200_OK)

        login = self.client.post(
            "/api/v1/auth/token/", {"username": self.user.username, "password": "Newpass123"}, format="json"
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh(self):
        login = self.client.post(
            "/api/v1/auth/token/", {"username": self.user.username, "password": self.password}, format="json"
        )
        refresh = login.data["refresh"]
        access = login.data["access"]

        auth_client = APIClient()
        auth_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout = auth_client.post("/api/v1/accounts/logout/", {"refresh": refresh}, format="json")
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        refresh_resp = self.client.post("/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)
