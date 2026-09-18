from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from apps.cards.models import VCard
from apps.cards.services import can_manage_vcard
from apps.directory.search import search_directory
from apps.directory.serializers import DirectoryEntrySerializer, DirectoryVisibilitySerializer


class PublicDirectorySearchView(ListAPIView):
    """GET /directory/?q=&category=&location=&industry=&company=&profession=
    (§35). Unauthenticated, rate-limited, only opted-in public cards."""

    serializer_class = DirectoryEntrySerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "directory-search"

    def get_queryset(self):
        params = self.request.query_params
        return search_directory(
            q=params.get("q", ""), category=params.get("category", ""),
            location=params.get("location", ""), industry=params.get("industry", ""),
            company=params.get("company", ""), profession=params.get("profession", ""),
        )


class DirectoryVisibilityView(RetrieveUpdateAPIView):
    """Authenticated: toggle a card's own directory visibility/category
    (§6 comment: 'visibility toggle, category assignment')."""

    serializer_class = DirectoryVisibilitySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "vcard_id"

    def get_object(self):
        vcard = get_object_or_404(VCard, id=self.kwargs["vcard_id"])
        if not can_manage_vcard(self.request.user, vcard):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to manage this card.")
        return vcard
