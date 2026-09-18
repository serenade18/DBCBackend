from rest_framework import serializers

from apps.cards.models import VCard
from apps.profile_blocks.serializers import (
    GalleryItemSerializer,
    ProductSerializer,
    ProfileBlockSerializer,
    ProfileLinkSerializer,
    ServiceSerializer,
    TestimonialSerializer,
)
from apps.templates.serializers import CardTemplateSerializer


class VCardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = VCard
        fields = [
            "id", "slug", "display_name", "job_title", "company_name", "profile_photo",
            "status", "visibility", "is_featured", "is_verified", "organization", "created_at", "updated_at",
        ]
        read_only_fields = fields


class VCardSerializer(serializers.ModelSerializer):
    public_url = serializers.CharField(read_only=True)

    class Meta:
        model = VCard
        fields = [
            "id", "organization", "owner", "assigned_user", "slug", "display_name", "job_title",
            "company_name", "bio", "profile_photo", "cover_photo", "email", "phone", "whatsapp",
            "website", "address", "location", "industry", "template", "theme_config", "visibility",
            "status", "is_featured", "is_verified", "is_directory_visible", "public_url", "published_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "organization", "owner", "assigned_user", "slug", "status",
            "is_featured", "is_verified", "public_url", "published_at", "created_at", "updated_at",
        ]


class VCardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VCard
        fields = [
            "id", "organization", "display_name", "job_title", "company_name", "bio",
            "profile_photo", "cover_photo", "email", "phone", "whatsapp", "website",
            "address", "location", "industry", "template", "theme_config", "visibility",
        ]
        read_only_fields = ["id"]


class VCardPublicSerializer(serializers.ModelSerializer):
    """Only fields that are safe to expose with no authentication (§35, §36:
    never private analytics/billing/internal org info)."""

    template = CardTemplateSerializer(read_only=True)
    links = ProfileLinkSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    testimonials = TestimonialSerializer(many=True, read_only=True)
    gallery_items = GalleryItemSerializer(many=True, read_only=True)
    blocks = ProfileBlockSerializer(many=True, read_only=True)

    class Meta:
        model = VCard
        fields = [
            "slug", "display_name", "job_title", "company_name", "bio", "profile_photo",
            "cover_photo", "email", "phone", "whatsapp", "website", "address", "location",
            "template", "theme_config", "links", "services", "products", "testimonials",
            "gallery_items", "blocks",
        ]
        read_only_fields = fields
