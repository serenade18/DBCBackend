from rest_framework import serializers

from apps.cards.models import VCard


class DirectoryEntrySerializer(serializers.ModelSerializer):
    """§36: only what's safe for a public listing — never private email,
    private phone, internal org info, analytics, or billing data."""

    class Meta:
        model = VCard
        fields = [
            "slug", "display_name", "job_title", "company_name", "location",
            "industry", "bio", "profile_photo", "is_verified",
        ]
        read_only_fields = fields


class DirectoryVisibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VCard
        fields = ["is_directory_visible", "industry"]
