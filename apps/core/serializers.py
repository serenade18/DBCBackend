from rest_framework import serializers


class DetailMessageSerializer(serializers.Serializer):
    """Generic {"detail": "..."} response shape used by several plain
    APIViews across the project — documented once here for OpenAPI/Postman."""

    detail = serializers.CharField()


class HealthSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["healthy", "unhealthy"])
    database = serializers.ChoiceField(choices=["healthy", "unhealthy"])
    redis = serializers.ChoiceField(choices=["healthy", "unhealthy"])


class ComponentHealthSerializer(serializers.Serializer):
    database = serializers.ChoiceField(choices=["healthy", "unhealthy"], required=False)
    redis = serializers.ChoiceField(choices=["healthy", "unhealthy"], required=False)
