from rest_framework import permissions

from apps.core.permissions import get_member_role


class IsOrganizationMemberObj(permissions.BasePermission):
    """For views where the object itself IS the Organization."""

    def has_object_permission(self, request, view, obj):
        return get_member_role(request.user, obj) is not None


class IsOrganizationAdminOrOwnerObj(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return get_member_role(request.user, obj) in {"owner", "admin"}


class IsOrganizationOwnerObj(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return get_member_role(request.user, obj) == "owner"
