from django.apps import AppConfig


class KanbanAppConfig(AppConfig):
    """App holding boards, tasks and comments."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kanban_app'
