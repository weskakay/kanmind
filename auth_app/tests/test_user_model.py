from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from auth_app.models import User

PASSWORD = 'kanmind-4711!'


class UserModelTests(TestCase):
    """Covers the user model and its manager."""

    def test_str_returns_email(self):
        user = User.objects.create_user('ada@example.com', 'Ada', PASSWORD)
        self.assertEqual(str(user), 'ada@example.com')

    def test_email_is_normalized(self):
        user = User.objects.create_user('ada@EXAMPLE.COM', 'Ada', PASSWORD)
        self.assertEqual(user.email, 'ada@example.com')

    def test_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user('', 'Ada', PASSWORD)

    def test_superuser_has_admin_rights(self):
        admin = User.objects.create_superuser(
            'root@example.com', 'Root', PASSWORD,
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class CreateGuestUserCommandTests(TestCase):
    """Covers the create_guest_user management command."""

    def test_command_creates_the_guest_user(self):
        call_command('create_guest_user', stdout=StringIO())
        guest = User.objects.get(email='kevin@kovacsi.de')
        self.assertTrue(guest.check_password('asdasdasd'))

    def test_command_can_run_twice(self):
        call_command('create_guest_user', stdout=StringIO())
        call_command('create_guest_user', stdout=StringIO())
        self.assertEqual(User.objects.count(), 1)
