from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import User


class RegistrationTests(APITestCase):
    """Covers POST /api/registration/."""

    def setUp(self):
        self.url = reverse('registration')
        self.payload = {
            'fullname': 'Ada Lovelace',
            'email': 'ada@example.com',
            'password': 'kanmind-4711!',
            'repeated_password': 'kanmind-4711!',
        }

    def test_registration_returns_201_and_token(self):
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['email'], 'ada@example.com')
        self.assertEqual(response.data['fullname'], 'Ada Lovelace')
        self.assertEqual(response.data['user_id'], User.objects.first().id)

    def test_password_is_stored_hashed(self):
        self.client.post(self.url, self.payload)
        user = User.objects.get(email='ada@example.com')
        self.assertNotEqual(user.password, 'kanmind-4711!')
        self.assertTrue(user.check_password('kanmind-4711!'))

    def test_mismatched_passwords_return_400(self):
        self.payload['repeated_password'] = 'something-else'
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_duplicate_email_returns_400(self):
        self.client.post(self.url, self.payload)
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_missing_fields_return_400(self):
        response = self.client.post(self.url, {'email': 'a@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_returns_400(self):
        self.payload['password'] = '1'
        self.payload['repeated_password'] = '1'
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_email_is_stored_in_lower_case(self):
        self.payload['email'] = 'Ada.Lovelace@Example.com'
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'ada.lovelace@example.com')

    def test_same_email_in_other_case_returns_400(self):
        self.client.post(self.url, self.payload)
        self.payload['email'] = 'ADA@example.com'
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_email_returns_400(self):
        self.payload['email'] = 'not-an-email'
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
