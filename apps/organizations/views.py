from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.exceptions import EntitlementError
from apps.core.permissions import get_member_role
from apps.core.utils import log_audit_event
from apps.organizations.models import MembershipStatus, Organization, OrganizationMember, OrganizationRole
from apps.organizations.permissions import IsOrganizationAdminOrOwnerObj, IsOrganizationMemberObj
from apps.organizations.serializers import (
    MemberInviteSerializer,
    MemberUpdateSerializer,
    OrganizationMemberSerializer,
    OrganizationSerializer,
)

User = get_user_model()


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return Organization.objects.filter(
            members__user=self.request.user, members__status=MembershipStatus.ACTIVE
        ).distinct().order_by("name")

    def get_permissions(self):
        if self.action in {"partial_update", "update"}:
            return [IsAuthenticated(), IsOrganizationAdminOrOwnerObj()]
        return super().get_permissions()

    def perform_create(self, serializer):
        base_slug = slugify(serializer.validated_data["name"])
        slug = base_slug
        suffix = 1
        while Organization.objects.filter(slug=slug).exists():
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        organization = serializer.save(slug=slug)
        OrganizationMember.objects.create(
            organization=organization,
            user=self.request.user,
            role=OrganizationRole.OWNER,
            status=MembershipStatus.ACTIVE,
            joined_at=timezone.now(),
        )
        log_audit_event(
            actor=self.request.user, organization=organization, action="organization.created",
            resource_type="organization", resource_id=organization.id, request=self.request,
        )

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated, IsOrganizationMemberObj])
    def members(self, request, pk=None):
        organization = self.get_object()
        memberships = organization.members.select_related("user").exclude(status=MembershipStatus.REMOVED)
        serializer = OrganizationMemberSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="members/invite",
            permission_classes=[IsAuthenticated, IsOrganizationAdminOrOwnerObj])
    def invite_member(self, request, pk=None):
        organization = self.get_object()

        from apps.billing.services import EntitlementService

        active_count = organization.members.filter(status__in=[MembershipStatus.ACTIVE, MembershipStatus.INVITED]).count()
        if not EntitlementService(organization).can_add_team_member(active_count):
            raise EntitlementError("Team member limit reached for the current plan.")

        serializer = MemberInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        role = serializer.validated_data["role"]

        user, _ = User.objects.get_or_create(email=email, defaults={"is_active": True})

        membership, created = OrganizationMember.objects.get_or_create(
            organization=organization, user=user,
            defaults={"role": role, "status": MembershipStatus.INVITED},
        )
        if not created:
            if membership.status == MembershipStatus.REMOVED:
                membership.status = MembershipStatus.INVITED
                membership.role = role
                membership.save(update_fields=["status", "role"])
            else:
                return Response({"detail": "User is already a member or has a pending invite."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.notifications.tasks import send_team_invitation_email

        # Direct call, not .delay() — no Celery worker required; see
        # apps.accounts.views._send_verification_email.
        send_team_invitation_email(str(membership.id))
        log_audit_event(
            actor=request.user, organization=organization, action="organization.member_invited",
            resource_type="organization_member", resource_id=membership.id, request=request,
            metadata={"email": email, "role": role},
        )
        return Response(OrganizationMemberSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"], url_path="members/(?P<member_id>[^/.]+)",
            permission_classes=[IsAuthenticated, IsOrganizationAdminOrOwnerObj])
    def member_detail(self, request, pk=None, member_id=None):
        organization = self.get_object()
        membership = organization.members.exclude(status=MembershipStatus.REMOVED).filter(id=member_id).first()
        if not membership:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if membership.role == OrganizationRole.OWNER:
            return Response({"detail": "The organization owner cannot be modified or removed here."}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == "DELETE":
            membership.status = MembershipStatus.REMOVED
            membership.save(update_fields=["status"])
            log_audit_event(
                actor=request.user, organization=organization, action="organization.member_removed",
                resource_type="organization_member", resource_id=membership.id, request=request,
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = MemberUpdateSerializer(membership, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("status") == MembershipStatus.ACTIVE and not membership.joined_at:
            membership.joined_at = timezone.now()
        serializer.save()

        log_audit_event(
            actor=request.user, organization=organization, action="organization.member_updated",
            resource_type="organization_member", resource_id=membership.id, request=request,
        )
        return Response(OrganizationMemberSerializer(membership).data)
