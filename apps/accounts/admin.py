from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "first_name", "last_name", "is_active", "is_staff", "platform_role", "date_joined"]
    list_filter = ["is_active", "is_staff", "platform_role", "email_verified"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    readonly_fields = ["id", "date_joined", "updated_at", "last_login"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone", "avatar")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "platform_role", "email_verified", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "is_staff", "is_active")}),
    )
    filter_horizontal = ["groups", "user_permissions"]
