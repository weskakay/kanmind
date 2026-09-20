from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import UserSerializer
from auth_app.models import User
from kanban_app.api.permissions import (
    IsBoardMemberOrOwner, IsBoardOwner, IsCommentAuthor, IsTaskBoardMember,
    IsTaskCreatorOrBoardOwner,
)
from kanban_app.api.serializers import (
    BoardDetailSerializer, BoardSummarySerializer, BoardUpdateSerializer,
    CommentSerializer, TaskSerializer, TaskUpdateSerializer,
)
from kanban_app.models import Board, Comment, Task


def get_task_for_member(user, task_id):
    """Return the task from the url, board members and owner only."""
    task = get_object_or_404(Task, pk=task_id)
    board = task.board
    if board.owner_id == user.id:
        return task
    if not board.members.filter(pk=user.pk).exists():
        raise PermissionDenied('You are not a member of this board.')
    return task


class BoardListCreateView(generics.ListCreateAPIView):
    """GET lists the boards of the user, POST creates a new one."""

    queryset = Board.objects.all()
    serializer_class = BoardSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return boards the user owns or is a member of."""
        user = self.request.user
        return Board.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().prefetch_related('members', 'tasks')

    def perform_create(self, serializer):
        """Store the logged in user as the owner."""
        serializer.save(owner=self.request.user)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Read, update or delete a single board."""

    queryset = Board.objects.prefetch_related(
        'members',
        'tasks__assignee',
        'tasks__reviewer',
        'tasks__comments',
    )
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        """Only the owner may delete, members may read and update."""
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsBoardOwner()]
        return [IsAuthenticated(), IsBoardMemberOrOwner()]

    def get_serializer_class(self):
        """Use the update serializer for PATCH."""
        if self.request.method == 'PATCH':
            return BoardUpdateSerializer
        return BoardDetailSerializer


class EmailCheckView(APIView):
    """GET /api/email-check/ looks up a user by email address."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the user behind the given email address."""
        email = self.read_email(request)
        if email is None:
            return self.error('A valid email address is required.', 400)
        user = User.objects.filter(email=email).first()
        if user is None:
            return self.error('No user with this email address.', 404)
        return Response(UserSerializer(user).data)

    def error(self, detail, code):
        """Answer with a short message and the given status code."""
        return Response({'detail': detail}, status=code)

    def read_email(self, request):
        """Return the queried address, or None if it is not an email."""
        email = request.query_params.get('email', '').strip().lower()
        try:
            validate_email(email)
        except DjangoValidationError:
            return None
        return email


class TaskCreateView(generics.CreateAPIView):
    """POST /api/tasks/ creates a task on a board."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        """Resolve the board and its access before the body is read."""
        super().initial(request, *args, **kwargs)
        self.board = self.get_board()

    def get_board(self):
        """Return the board from the body, members and owner only."""
        board_id = str(self.request.data.get('board', ''))
        if not board_id.isdigit():
            raise ValidationError({'board': 'A board id is required.'})
        board = get_object_or_404(Board, pk=int(board_id))
        if board.owner_id == self.request.user.id:
            return board
        if not board.members.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied('You are not a member of this board.')
        return board

    def perform_create(self, serializer):
        """Store the logged in user as the creator."""
        serializer.save(created_by=self.request.user, board=self.board)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Update or delete a single task."""

    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer
    http_method_names = ['patch', 'delete', 'options']

    def get_permissions(self):
        """Members may update, only creator or board owner may delete."""
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        return [IsAuthenticated(), IsTaskBoardMember()]


class AssignedTaskListView(generics.ListAPIView):
    """GET /api/tasks/assigned-to-me/ lists the own tasks."""

    queryset = Task.objects.all()
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

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks to review, boards the user left aside."""
        return Task.objects.filter(
            reviewer=self.request.user,
            board__members=self.request.user,
        ).select_related('assignee', 'reviewer').prefetch_related('comments')


class CommentListCreateView(generics.ListCreateAPIView):
    """Lists and writes the comments of one task."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        """Look the task up before the request body is read."""
        super().initial(request, *args, **kwargs)
        self.task = get_task_for_member(request.user, self.kwargs['task_id'])

    def get_queryset(self):
        """Return the comments of that task, oldest first."""
        return self.task.comments.select_related('author')

    def perform_create(self, serializer):
        """Store the comment with its task and author."""
        serializer.save(task=self.task, author=self.request.user)


class CommentDetailView(generics.DestroyAPIView):
    """Deletes a single comment."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def initial(self, request, *args, **kwargs):
        """Look the task up before the comment is touched."""
        super().initial(request, *args, **kwargs)
        self.task = get_task_for_member(request.user, self.kwargs['task_id'])

    def get_queryset(self):
        """Limit the lookup to the comments of the task in the url."""
        return Comment.objects.filter(task=self.task)
