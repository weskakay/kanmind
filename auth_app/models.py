from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    """Creates users that log in with their email address."""

    use_in_migrations = True

    def create_user(self, email, fullname='', password=None, **extra):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Users must have an email address.')
        user = self.model(
            email=self.normalize_email(email).lower(),
            fullname=fullname,
            **extra,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, fullname='', password=None, **extra):
        """Create and save a user with admin access."""
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, fullname, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Account of a KanMind user, identified by email."""

    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']

    class Meta:
        ordering = ['id']
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email
