from rest_framework import serializers

from kanban_app.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """Comment as the frontend shows it, author is a plain name."""

    author = serializers.CharField(source='author.fullname', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
