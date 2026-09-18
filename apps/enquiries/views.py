from django.shortcuts import get_object_or_404, redirect
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.cards.models import VCard
from apps.cards.services import accessible_vcard_ids, can_manage_vcard
from apps.enquiries.models import Enquiry
from apps.enquiries.serializers import EnquirySerializer, EnquiryStatusUpdateSerializer, PublicEnquirySubmitSerializer


class EnquiryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "vcard"]

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return EnquiryStatusUpdateSerializer
        return EnquirySerializer

    def get_queryset(self):
        return Enquiry.objects.filter(vcard_id__in=accessible_vcard_ids(self.request.user))

    def get_object(self):
        obj = super().get_object()
        if not can_manage_vcard(self.request.user, obj.vcard):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to manage enquiries for this card.")
        return obj


class PublicEnquirySubmitView(APIView):
    """
    Unauthenticated submit endpoint (§18). Handles both a plain HTML <form>
    POST from the no-JS public card page (redirects back with ?sent=1) and a
    JSON POST from any future JS client (returns 201 JSON).
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "enquiry-submit"

    def post(self, request, vcard_slug):
        vcard = get_object_or_404(VCard, slug=vcard_slug)
        if not vcard.is_publicly_viewable:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PublicEnquirySubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enquiry = serializer.save(vcard=vcard)

        from apps.notifications.tasks import notify_new_enquiry

        notify_new_enquiry.delay(str(enquiry.id))

        if request.content_type == "application/json":
            return Response(EnquirySerializer(enquiry).data, status=status.HTTP_201_CREATED)
        return redirect(f"/@{vcard.slug}/?sent=1")
