from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from auth_app.api.serializers import UserSerializer
from auth_app.models import User
from kanban_app.models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Task with everything the board view needs."""

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source='reviewer',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'board',
            'title',
            'description',
            'status',
            'priority',
            'assignee',
            'assignee_id',
            'reviewer',
            'reviewer_id',
            'due_date',
            'comments_count',
        ]

    def check_access(self, board):
        """Refuse boards the requesting user is not a member of."""
        user = self.context['request'].user
        if not board.members.filter(pk=user.pk).exists():
            raise PermissionDenied('You are not a member of this board.')

    def get_comments_count(self, task):
        """Return how many comments the task has."""
        return 0

    def validate(self, attrs):
        """Assignee and reviewer have to be members of the board."""
        board = attrs.get('board') or getattr(self.instance, 'board', None)
        self.check_access(board)
        for field in ['assignee', 'reviewer']:
            user = attrs.get(field)
            if user and not board.members.filter(pk=user.pk).exists():
                raise serializers.ValidationError({
                    f'{field}_id': 'User is not a member of this board.',
                })
        return attrs


class BoardTaskSerializer(TaskSerializer):
    """Task as it appears inside a board, without the board field."""

    class Meta(TaskSerializer.Meta):
        fields = [
            field for field in TaskSerializer.Meta.fields
            if field != 'board'
        ]


class TaskUpdateSerializer(TaskSerializer):
    """Task as it is returned after an update."""

    class Meta(TaskSerializer.Meta):
        fields = [
            field for field in TaskSerializer.Meta.fields
            if field not in ['board', 'comments_count']
        ]
