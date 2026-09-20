from rest_framework.permissions import BasePermission


class IsBoardMemberOrOwner(BasePermission):
    """Allows access to the owner and to the members of a board."""

    def has_object_permission(self, request, view, obj):
        """Check membership, the owner always counts as a member."""
        return (
            obj.owner_id == request.user.id
            or obj.members.filter(pk=request.user.pk).exists()
        )


class IsBoardOwner(BasePermission):
    """Allows access only to the owner of a board."""

    def has_object_permission(self, request, view, obj):
        """Check ownership."""
        return obj.owner_id == request.user.id


class IsTaskBoardMember(BasePermission):
    """Allows access to everyone who shares the board of a task."""

    def has_object_permission(self, request, view, obj):
        """Check membership on the board the task belongs to."""
        return (
            obj.board.owner_id == request.user.id
            or obj.board.members.filter(pk=request.user.pk).exists()
        )


class IsTaskCreatorOrBoardOwner(BasePermission):
    """Allows the board owner and the creator to remove a task."""

    def has_object_permission(self, request, view, obj):
        """Members who left the board lose this right as well."""
        board = obj.board
        if board.owner_id == request.user.id:
            return True
        if not board.members.filter(pk=request.user.pk).exists():
            return False
        return obj.created_by_id == request.user.id
