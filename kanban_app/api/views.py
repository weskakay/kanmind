from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import UserSerializer
from auth_app.models import User
from kanban_app.api.permissions import IsBoardMemberOrOwner, IsBoardOwner
from kanban_app.api.serializers import (
    BoardDetailSerializer, BoardSummarySerializer, BoardUpdateSerializer,
)
from kanban_app.models import Board


class BoardListCreateView(generics.ListCreateAPIView):
    """GET lists the boards of the user, POST creates a new one."""

    serializer_class = BoardSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return boards the user owns or is a member of."""
        user = self.request.user
        own = Board.objects.filter(Q(owner=user) | Q(members=user))
        return Board.objects.filter(
            pk__in=own.values('pk')
        ).prefetch_related('members', 'tasks')

    def perform_create(self, serializer):
        """Store the logged in user as the owner."""
        serializer.save(owner=self.request.user)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Read, update or delete a single board."""

    queryset = Board.objects.prefetch_related(
        'members', 'tasks__assignee', 'tasks__reviewer',
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
        email = request.query_params.get('email', '').strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {'detail': 'A valid email address is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.filter(email=email).first()
        if user is None:
            return Response(
                {'detail': 'No user with this email address.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(UserSerializer(user).data)
