from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import User


class LoginTests(APITestCase):
    """Covers POST /api/login/."""

    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(
            email='ada@example.com',
            fullname='Ada Lovelace',
            password='kanmind-4711!',
        )

    def test_login_returns_200_and_token(self):
        response = self.client.post(self.url, {
            'email': 'ada@example.com',
            'password': 'kanmind-4711!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = Token.objects.get(user=self.user)
        self.assertEqual(response.data['token'], token.key)
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_login_twice_reuses_the_same_token(self):
        first = self.client.post(self.url, {
            'email': 'ada@example.com',
            'password': 'kanmind-4711!',
        })
        second = self.client.post(self.url, {
            'email': 'ada@example.com',
            'password': 'kanmind-4711!',
        })
        self.assertEqual(first.data['token'], second.data['token'])

    def test_login_works_with_mixed_case_email(self):
        response = self.client.post(self.url, {
            'email': 'Ada@Example.com',
            'password': 'kanmind-4711!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_wrong_password_returns_400(self):
        response = self.client.post(self.url, {
            'email': 'ada@example.com',
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_email_returns_400(self):
        response = self.client.post(self.url, {
            'email': 'nobody@example.com',
            'password': 'kanmind-4711!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        response = self.client.post(self.url, {'email': 'ada@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
