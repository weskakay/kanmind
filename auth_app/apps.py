from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """App holding the custom user model and the auth endpoints."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'
