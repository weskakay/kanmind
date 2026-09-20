from django.contrib import admin

from kanban_app.models import Board


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Read and edit boards in the Django admin."""

    list_display = ['id', 'title', 'owner']
    search_fields = ['title']
    filter_horizontal = ['members']
