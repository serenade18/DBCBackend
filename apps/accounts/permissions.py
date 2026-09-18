from rest_framework import permissions


class IsPlatformStaff(permissions.BasePermission):
    """Platform-level roles (§5): super_admin, admin, support, finance."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.platform_role))


class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user
