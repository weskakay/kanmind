from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from kanban_app.api.permissions import (
    IsTaskBoardMember, IsTaskCreatorOrBoardOwner,
)
from kanban_app.api.task_serializers import (
    TaskSerializer, TaskUpdateSerializer,
)
from kanban_app.models import Task


class TaskCreateView(generics.CreateAPIView):
    """POST /api/tasks/ creates a task on a board."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Store the logged in user as the creator."""
        serializer.save(created_by=self.request.user)


class TaskDetailView(generics.UpdateAPIView, generics.DestroyAPIView):
    """Update or delete a single task."""

    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer
    http_method_names = ['patch', 'delete', 'head', 'options']

    def get_permissions(self):
        """Members may update, only creator or board owner may delete."""
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        return [IsAuthenticated(), IsTaskBoardMember()]


class AssignedTaskListView(generics.ListAPIView):
    """GET /api/tasks/assigned-to-me/ lists the own tasks."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks the user has to work on, boards they left aside."""
        return Task.objects.filter(
            assignee=self.request.user,
            board__members=self.request.user,
        ).select_related('assignee', 'reviewer').prefetch_related('comments')


class ReviewingTaskListView(generics.ListAPIView):
    """GET /api/tasks/reviewing/ lists the tasks to review."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks to review, boards the user left aside."""
        return Task.objects.filter(
            reviewer=self.request.user,
            board__members=self.request.user,
        ).select_related('assignee', 'reviewer').prefetch_related('comments')
