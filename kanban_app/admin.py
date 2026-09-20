from django.contrib import admin

from kanban_app.models import Board, Comment, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Read and edit boards in the Django admin."""

    list_display = ['id', 'title', 'owner']
    search_fields = ['title']
    filter_horizontal = ['members']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Read and edit tasks in the Django admin."""

    list_display = ['id', 'title', 'board', 'status', 'priority']
    list_filter = ['status', 'priority']
    search_fields = ['title']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Read and edit comments in the Django admin."""

    list_display = ['id', 'task', 'author', 'created_at']
    list_select_related = ['task', 'author']
    search_fields = ['content']
