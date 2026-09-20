from django.conf import settings
from django.db import models


class Board(models.Model):
    """A kanban board owned by one user and shared with members."""

    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_boards',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='boards',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title
