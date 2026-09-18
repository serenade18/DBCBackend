from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from apps.templates.models import CardTemplate
from apps.templates.serializers import CardTemplateSerializer


class CardTemplateViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CardTemplateSerializer
    permission_classes = [AllowAny]
    queryset = CardTemplate.objects.filter(is_active=True)
    filterset_fields = ["category", "is_premium"]
