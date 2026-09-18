from rest_framework import serializers

from apps.templates.models import CardTemplate


class CardTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardTemplate
        fields = ["id", "name", "slug", "preview_image", "category", "configuration", "is_premium"]
        read_only_fields = fields
