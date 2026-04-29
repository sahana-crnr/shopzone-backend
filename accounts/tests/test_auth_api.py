from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class AuthApiTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.refresh_url = reverse("token_refresh")
        self.me_url = reverse("me")
        self.user_payload = {
            "name": "Admin",
            "email": "admin@shop.com",
            "phone": "1234567890",
            "password": "adminpass123",
        }

    def test_successful_register(self):
        response = self.client.post(self.register_url, self.user_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data["email"], self.user_payload["email"])

    def test_duplicate_email_register_failure(self):
        self.client.post(self.register_url, self.user_payload, format="json")
        response = self.client.post(self.register_url, self.user_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_successful_login_returns_access_and_refresh(self):
        User.objects.create_user(
            name=self.user_payload["name"],
            email=self.user_payload["email"],
            phone=self.user_payload["phone"],
            password=self.user_payload["password"],
        )

        response = self.client.post(
            self.login_url,
            {
                "email": self.user_payload["email"],
                "password": self.user_payload["password"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_returns_new_access_token(self):
        user = User.objects.create_user(
            name=self.user_payload["name"],
            email=self.user_payload["email"],
            phone=self.user_payload["phone"],
            password=self.user_payload["password"],
        )
        refresh = RefreshToken.for_user(user)

        response = self.client.post(
            self.refresh_url,
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_me_unauthorized_without_token(self):
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_success_with_valid_token(self):
        user = User.objects.create_user(
            name=self.user_payload["name"],
            email=self.user_payload["email"],
            phone=self.user_payload["phone"],
            password=self.user_payload["password"],
        )
        access = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_payload["email"])
