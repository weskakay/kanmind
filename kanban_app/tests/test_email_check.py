from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import User

PASSWORD = 'kanmind-4711!'


class EmailCheckTests(APITestCase):
    """Covers GET /api/email-check/."""

    def setUp(self):
        self.url = reverse('email-check')
        self.user = User.objects.create_user(
            'ada@example.com', 'Ada Lovelace', PASSWORD,
        )

    def test_known_email_returns_the_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {'email': 'ada@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fullname'], 'Ada Lovelace')
        self.assertEqual(response.data['id'], self.user.id)

    def test_lookup_ignores_upper_case(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {'email': 'Ada@Example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_email_returns_404(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {'email': 'nobody@example.com'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_email_returns_400(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email_returns_400(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {'email': 'not-an-email'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requires_authentication(self):
        response = self.client.get(self.url, {'email': 'ada@example.com'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
