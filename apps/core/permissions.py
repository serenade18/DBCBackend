from rest_framework import permissions


def get_active_memberships(user):
    if not user or not user.is_authenticated:
        return []
    return list(
        user.organization_memberships.filter(status="active").select_related("organization")
    )


def get_member_role(user, organization):
    if not user or not user.is_authenticated or organization is None:
        return None
    membership = user.organization_memberships.filter(
        organization=organization, status="active"
    ).first()
    return membership.role if membership else None


class IsOrganizationMember(permissions.BasePermission):
    """Object must expose `.organization`. Individually-owned resources
    (organization is None) are scoped to `.owner` instead."""

    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", None)
        if organization is None:
            owner = getattr(obj, "owner", None)
            return owner is not None and owner == request.user
        role = get_member_role(request.user, organization)
        return role is not None


class IsOrganizationAdminOrOwner(permissions.BasePermission):
    """Requires org role of owner/admin, or personal ownership for
    org-less resources."""

    allowed_roles = {"owner", "admin"}

    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", None)
        if organization is None:
            owner = getattr(obj, "owner", None)
            return owner is not None and owner == request.user
        role = get_member_role(request.user, organization)
        return role in self.allowed_roles


class IsOrganizationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", None)
        if organization is None:
            owner = getattr(obj, "owner", None)
            return owner is not None and owner == request.user
        return get_member_role(request.user, organization) == "owner"


class IsCardOwnerAdminOrAssignee(permissions.BasePermission):
    """VCard-specific: owner, org admin/owner, or the user the card is
    assigned to (assignee may edit content but not delete/reassign — views
    should further gate destructive actions)."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if obj.owner_id == user.id:
            return True
        if obj.assigned_user_id == user.id:
            return True
        if obj.organization_id:
            return get_member_role(user, obj.organization) in {"owner", "admin"}
        return False
