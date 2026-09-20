from django.core.management.base import BaseCommand

from auth_app.models import User

GUEST_EMAIL = 'kevin@kovacsi.de'
GUEST_PASSWORD = 'asdasdasd'
GUEST_FULLNAME = 'Kevin Kovacsi'


class Command(BaseCommand):
    """Creates the guest account the frontend logs in with."""

    help = 'Create the guest user used by the KanMind frontend.'

    def handle(self, *args, **options):
        """Create the guest user unless it already exists."""
        user = User.objects.filter(email=GUEST_EMAIL).first()
        if user:
            self.stdout.write('Guest user already exists.')
            return
        User.objects.create_user(
            email=GUEST_EMAIL,
            fullname=GUEST_FULLNAME,
            password=GUEST_PASSWORD,
        )
        self.stdout.write(f'Created guest user {GUEST_EMAIL}.')
