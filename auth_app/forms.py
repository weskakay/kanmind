from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from auth_app.models import User


class UserAdminCreationForm(UserCreationForm):
    """Creates a user in the admin with a hashed password."""

    class Meta:
        model = User
        fields = ['email', 'fullname']


class UserAdminChangeForm(UserChangeForm):
    """Edits a user in the admin without exposing the password hash."""

    class Meta:
        model = User
        fields = ['email', 'fullname', 'is_active', 'is_staff']
