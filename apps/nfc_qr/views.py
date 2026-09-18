from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsPlatformStaff
from apps.cards.models import VCard
from apps.core.permissions import get_active_memberships
from apps.core.utils import log_audit_event
from apps.nfc_qr.models import NfcCard
from apps.nfc_qr.nfc import (
    NfcTransitionError,
    activate_card,
    assign_card,
    reassign_card,
    retire_card,
    suspend_card,
    write_instructions,
)
from apps.nfc_qr.serializers import NfcAssignSerializer, NfcCardSerializer, NfcRegisterSerializer


class NfcCardViewSet(viewsets.ModelViewSet):
    serializer_class = NfcCardSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.is_platform_staff:
            return NfcCard.objects.all()

        org_ids = [m.organization_id for m in get_active_memberships(user)]
        return NfcCard.objects.filter(
            Q(vcard__owner=user)
            | Q(vcard__organization_id__in=org_ids)
            | Q(order__organization_id__in=org_ids)
            | Q(order__customer=user)
        ).distinct()

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsPlatformStaff()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = NfcRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nfc_card = serializer.save()
        log_audit_event(actor=request.user, action="nfc.registered", resource_type="nfc_card", resource_id=nfc_card.id, request=request)
        return Response(NfcCardSerializer(nfc_card).data, status=status.HTTP_201_CREATED)

    def _get_owned_vcard(self, request, vcard_id):
        user = request.user
        org_ids = [m.organization_id for m in get_active_memberships(user)]
        return VCard.objects.filter(Q(id=vcard_id) & (Q(owner=user) | Q(organization_id__in=org_ids))).first()

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        nfc_card = self.get_object()
        serializer = NfcAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vcard = self._get_owned_vcard(request, serializer.validated_data["vcard_id"])
        if not vcard:
            return Response({"detail": "VCard not found or not accessible."}, status=status.HTTP_404_NOT_FOUND)

        try:
            assign_card(nfc_card, vcard)
        except NfcTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_audit_event(actor=request.user, action="nfc.assigned", resource_type="nfc_card", resource_id=nfc_card.id, request=request)
        return Response(NfcCardSerializer(nfc_card).data)

    @action(detail=True, methods=["post"])
    def reassign(self, request, pk=None):
        nfc_card = self.get_object()
        serializer = NfcAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vcard = self._get_owned_vcard(request, serializer.validated_data["vcard_id"])
        if not vcard:
            return Response({"detail": "VCard not found or not accessible."}, status=status.HTTP_404_NOT_FOUND)

        try:
            reassign_card(nfc_card, vcard)
        except NfcTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_audit_event(actor=request.user, action="nfc.reassigned", resource_type="nfc_card", resource_id=nfc_card.id, request=request)
        return Response(NfcCardSerializer(nfc_card).data)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        nfc_card = self.get_object()
        try:
            activate_card(nfc_card)
        except NfcTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(NfcCardSerializer(nfc_card).data)

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        nfc_card = self.get_object()
        try:
            suspend_card(nfc_card)
        except NfcTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(NfcCardSerializer(nfc_card).data)

    @action(detail=True, methods=["post"])
    def retire(self, request, pk=None):
        nfc_card = self.get_object()
        retire_card(nfc_card)
        return Response(NfcCardSerializer(nfc_card).data)

    @action(detail=True, methods=["get"], url_path="write-instructions")
    def write_instructions_view(self, request, pk=None):
        nfc_card = self.get_object()
        return Response(write_instructions(nfc_card))
