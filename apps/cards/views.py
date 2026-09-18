from django.db.models import Q
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.billing.services import EntitlementService
from apps.cards.models import VCard
from apps.cards.serializers import VCardCreateSerializer, VCardListSerializer, VCardSerializer
from apps.cards.services import (
    assign_vcard,
    can_manage_vcard,
    generate_unique_slug,
    publish_vcard,
    unassign_vcard,
    unpublish_vcard,
)
from apps.core.exceptions import EntitlementError
from apps.core.permissions import get_active_memberships, get_member_role
from apps.core.utils import log_audit_event
from apps.nfc_qr.qr import generate_qr_for_vcard
from apps.nfc_qr.vcard import build_vcf


class VCardViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return VCardListSerializer
        if self.action == "create":
            return VCardCreateSerializer
        return VCardSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = [m.organization_id for m in get_active_memberships(user)]
        return VCard.objects.filter(
            Q(owner=user) | Q(assigned_user=user) | Q(organization_id__in=org_ids)
        ).distinct()

    def get_object(self):
        obj = super().get_object()
        if not can_manage_vcard(self.request.user, obj) and self.action not in {"retrieve"}:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to manage this card.")
        return obj

    def perform_create(self, serializer):
        user = self.request.user
        organization = serializer.validated_data.get("organization")
        if organization and get_member_role(user, organization) not in {"owner", "admin"}:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to create cards for this organization.")

        tenant = organization or user
        entitlement = EntitlementService(tenant)
        if not entitlement.can_create_vcard():
            raise EntitlementError("VCard limit reached for the current plan.")

        slug = generate_unique_slug(serializer.validated_data.get("display_name", "card"))
        vcard = serializer.save(owner=user, slug=slug)
        log_audit_event(
            actor=user, organization=organization, action="card.created",
            resource_type="vcard", resource_id=vcard.id, request=self.request,
        )

    def perform_update(self, serializer):
        vcard = serializer.save()
        log_audit_event(
            actor=self.request.user, organization=vcard.organization, action="card.updated",
            resource_type="vcard", resource_id=vcard.id, request=self.request,
        )

    def perform_destroy(self, instance):
        log_audit_event(
            actor=self.request.user, organization=instance.organization, action="card.deleted",
            resource_type="vcard", resource_id=instance.id, request=self.request,
        )
        instance.delete()

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        vcard = self.get_object()
        errors = publish_vcard(vcard)
        if errors:
            return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)
        log_audit_event(
            actor=request.user, organization=vcard.organization, action="card.published",
            resource_type="vcard", resource_id=vcard.id, request=request,
        )
        return Response(VCardSerializer(vcard).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        vcard = self.get_object()
        unpublish_vcard(vcard)
        log_audit_event(
            actor=request.user, organization=vcard.organization, action="card.unpublished",
            resource_type="vcard", resource_id=vcard.id, request=request,
        )
        return Response(VCardSerializer(vcard).data)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        vcard = self.get_object()
        if not vcard.organization_id:
            return Response({"detail": "Only organization-owned cards can be assigned."}, status=status.HTTP_400_BAD_REQUEST)
        if get_member_role(request.user, vcard.organization) not in {"owner", "admin"}:
            return Response(status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get("user_id")
        from apps.accounts.models import User

        target_user = User.objects.filter(
            id=user_id, organization_memberships__organization=vcard.organization,
            organization_memberships__status="active",
        ).first()
        if not target_user:
            return Response({"detail": "User is not an active member of this organization."}, status=status.HTTP_400_BAD_REQUEST)

        assign_vcard(vcard, target_user)
        log_audit_event(
            actor=request.user, organization=vcard.organization, action="card.assigned",
            resource_type="vcard", resource_id=vcard.id, request=request, metadata={"assigned_to": str(target_user.id)},
        )
        return Response(VCardSerializer(vcard).data)

    @action(detail=True, methods=["post"])
    def unassign(self, request, pk=None):
        vcard = self.get_object()
        if vcard.organization_id and get_member_role(request.user, vcard.organization) not in {"owner", "admin"}:
            return Response(status=status.HTTP_403_FORBIDDEN)
        unassign_vcard(vcard)
        log_audit_event(
            actor=request.user, organization=vcard.organization, action="card.unassigned",
            resource_type="vcard", resource_id=vcard.id, request=request,
        )
        return Response(VCardSerializer(vcard).data)

    @action(detail=True, methods=["get"])
    def qr(self, request, pk=None):
        vcard = self.get_object()
        fmt = request.query_params.get("format", "png")
        try:
            content, content_type = generate_qr_for_vcard(vcard, fmt)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return HttpResponse(content, content_type=content_type)

    @action(detail=True, methods=["get"])
    def contact(self, request, pk=None):
        vcard = self.get_object()
        vcf_bytes = build_vcf(vcard)
        response = HttpResponse(vcf_bytes, content_type="text/vcard")
        response["Content-Disposition"] = f'attachment; filename="{vcard.slug}.vcf"'
        return response
