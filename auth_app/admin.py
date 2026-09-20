from django.contrib import admin

from auth_app.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Read and edit user accounts in the Django admin."""

    list_display = ['id', 'email', 'fullname', 'is_staff']
    search_fields = ['email', 'fullname']
    ordering = ['id']
