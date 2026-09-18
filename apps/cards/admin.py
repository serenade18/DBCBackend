from django.contrib import admin

from apps.cards.models import VCard


@admin.register(VCard)
class VCardAdmin(admin.ModelAdmin):
    list_display = ["display_name", "slug", "owner", "organization", "status", "visibility", "is_featured", "is_verified", "created_at"]
    list_filter = ["status", "visibility", "is_featured", "is_verified", "is_directory_visible"]
    search_fields = ["display_name", "slug", "owner__email", "organization__name"]
    autocomplete_fields = ["owner", "assigned_user", "organization", "template"]
    readonly_fields = ["id", "public_url", "published_at", "created_at", "updated_at"]
