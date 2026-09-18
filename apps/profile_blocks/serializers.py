from rest_framework import serializers

from apps.profile_blocks.models import GalleryItem, Product, ProfileBlock, ProfileLink, Service, Testimonial


class ProfileBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileBlock
        fields = ["id", "vcard", "type", "title", "content", "position", "is_visible", "created_at", "updated_at"]
        read_only_fields = ["id", "vcard", "created_at", "updated_at"]


class ProfileLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileLink
        fields = ["id", "vcard", "title", "url", "icon", "position", "is_visible"]
        read_only_fields = ["id", "vcard"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "vcard", "name", "description", "price", "currency", "image", "booking_enabled", "position", "is_visible"]
        read_only_fields = ["id", "vcard"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "vcard", "name", "description", "price", "currency", "image", "external_url", "position", "is_visible"]
        read_only_fields = ["id", "vcard"]


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ["id", "vcard", "customer_name", "customer_title", "customer_photo", "content", "rating", "position", "is_visible"]
        read_only_fields = ["id", "vcard"]


class GalleryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryItem
        fields = ["id", "vcard", "image", "title", "description", "position", "is_visible"]
        read_only_fields = ["id", "vcard"]


class ReorderSerializer(serializers.Serializer):
    """Body: {"order": ["<id>", "<id>", ...]} — full ordering, front to back."""

    order = serializers.ListField(child=serializers.UUIDField())
