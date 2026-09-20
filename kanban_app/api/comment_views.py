from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from kanban_app.api.comment_serializers import CommentSerializer
from kanban_app.api.permissions import IsCommentAuthor
from kanban_app.models import Comment, Task


class TaskCommentAccessMixin:
    """Resolves the task from the url and gates it by board access."""

    def initial(self, request, *args, **kwargs):
        """Look the task up before the request body is read."""
        super().initial(request, *args, **kwargs)
        self.task = self.get_task()

    def get_task(self):
        """Return the task from the url, board members only."""
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        board = task.board
        if board.owner_id == self.request.user.id:
            return task
        if not board.members.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied('You are not a member of this board.')
        return task


class CommentListCreateView(TaskCommentAccessMixin,
                            generics.ListCreateAPIView):
    """Lists and writes the comments of one task."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the comments of that task, oldest first."""
        return self.task.comments.select_related('author')

    def perform_create(self, serializer):
        """Store the comment with its task and author."""
        serializer.save(task=self.task, author=self.request.user)


class CommentDetailView(TaskCommentAccessMixin, generics.DestroyAPIView):
    """Deletes a single comment."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def get_queryset(self):
        """Limit the lookup to the comments of the task in the url."""
        return Comment.objects.filter(task=self.task)
