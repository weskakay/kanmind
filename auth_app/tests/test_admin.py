from django.test import TestCase
from django.urls import reverse

from auth_app.models import User

PASSWORD = 'kanmind-4711!'


class UserAdminTests(TestCase):
    """Covers creating and editing users in the Django admin."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            'root@example.com', 'Root', PASSWORD,
        )
        self.client.force_login(self.admin)

    def test_new_user_gets_a_hashed_password(self):
        self.client.post(reverse('admin:auth_app_user_add'), {
            'email': 'new@example.com',
            'fullname': 'New User',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        user = User.objects.get(email='new@example.com')
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_change_form_does_not_expose_the_password(self):
        url = reverse('admin:auth_app_user_change', args=[self.admin.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.admin.password)

    def test_user_list_opens(self):
        response = self.client.get(reverse('admin:auth_app_user_changelist'))
        self.assertEqual(response.status_code, 200)
