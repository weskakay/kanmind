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
