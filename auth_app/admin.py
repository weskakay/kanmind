from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from auth_app.forms import UserAdminChangeForm, UserAdminCreationForm
from auth_app.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Read and edit user accounts in the Django admin."""

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    list_display = ['id', 'email', 'fullname', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'fullname']
    ordering = ['id']
    filter_horizontal = ['groups', 'user_permissions']
    fieldsets = [
        (None, {'fields': ['email', 'password']}),
        ('Personal info', {'fields': ['fullname']}),
        ('Permissions', {'fields': [
            'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions',
        ]}),
    ]
    add_fieldsets = [
        (None, {'fields': ['email', 'fullname', 'password1', 'password2']}),
    ]
