from rest_framework import serializers

from auth_app.api.serializers import UserSerializer
from auth_app.models import User
from kanban_app.models import Board, Comment, Task


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

    def get_comments_count(self, task):
        """Return how many comments the task has."""
        return len(task.comments.all())

    def validate(self, attrs):
        """Assignee and reviewer have to be members of the board."""
        board = attrs.get('board') or getattr(self.instance, 'board', None)
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
            'id',
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


class TaskUpdateSerializer(TaskSerializer):
    """Task as it is returned after an update."""

    class Meta(TaskSerializer.Meta):
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'assignee',
            'assignee_id',
            'reviewer',
            'reviewer_id',
            'due_date',
        ]


class BoardSummarySerializer(serializers.ModelSerializer):
    """Board with its counters, used by the board list and on create."""

    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False,
        write_only=True,
    )
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'members',
            'member_count',
            'ticket_count',
            'tasks_to_do_count',
            'tasks_high_prio_count',
            'owner_id',
        ]

    def get_member_count(self, board):
        """Return how many users share this board."""
        return len(board.members.all())

    def get_ticket_count(self, board):
        """Return how many tasks the board holds."""
        return len(board.tasks.all())

    def get_tasks_to_do_count(self, board):
        """Return how many tasks are still open."""
        return len([t for t in board.tasks.all() if t.status == 'to-do'])

    def get_tasks_high_prio_count(self, board):
        """Return how many tasks have a high priority."""
        return len([t for t in board.tasks.all() if t.priority == 'high'])

    def create(self, validated_data):
        """Save the board and make sure the owner is a member."""
        members = validated_data.pop('members', [])
        board = Board.objects.create(**validated_data)
        board.members.set(members)
        board.members.add(board.owner)
        return board


class BoardDetailSerializer(serializers.ModelSerializer):
    """Full board with its members and tasks."""

    owner_id = serializers.IntegerField(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Updates title and members, answers with owner and member data."""

    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False,
        write_only=True,
    )
    owner_data = UserSerializer(source='owner', read_only=True)
    members_data = UserSerializer(
        source='members',
        many=True,
        read_only=True,
    )

    class Meta:
        model = Board
        fields = ['id', 'title', 'members', 'owner_data', 'members_data']

    def update(self, instance, validated_data):
        """Replace the member list and keep the owner in it."""
        members = validated_data.pop('members', None)
        instance.title = validated_data.get('title', instance.title)
        instance.save()
        if members is not None:
            instance.members.set(members)
            instance.members.add(instance.owner)
        return instance


class CommentSerializer(serializers.ModelSerializer):
    """Comment as the frontend shows it, author is a plain name."""

    author = serializers.CharField(source='author.fullname', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
