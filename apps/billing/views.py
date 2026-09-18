from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Payment, Plan, Subscription, SubscriptionStatus
from apps.billing.serializers import (
    CheckoutResultSerializer,
    CheckoutSerializer,
    PaymentSerializer,
    PlanSerializer,
    SubscriptionSerializer,
)
from apps.billing.services import get_or_create_default_subscription, start_checkout
from apps.core.permissions import get_member_role
from apps.core.utils import log_audit_event
from apps.organizations.models import Organization


def resolve_tenant(request):
    """Resolves the (organization, owner) tenant pair billing endpoints act
    on: an explicit ?organization=<id> the user is a member of, or the
    individual user themselves."""
    org_id = request.query_params.get("organization") or request.data.get("organization_id")
    if org_id:
        organization = Organization.objects.filter(id=org_id).first()
        if not organization or get_member_role(request.user, organization) is None:
            return None, None
        return organization, None
    return None, request.user


class PlanListView(ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    queryset = Plan.objects.filter(is_active=True)


class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SubscriptionSerializer)
    def get(self, request):
        organization, owner = resolve_tenant(request)
        if organization is None and owner is None:
            return Response({"detail": "Not a member of that organization."}, status=status.HTTP_403_FORBIDDEN)
        subscription = get_or_create_default_subscription(organization=organization, owner=owner)
        return Response(SubscriptionSerializer(subscription).data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=CheckoutSerializer, responses={201: CheckoutResultSerializer})
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization, owner = resolve_tenant(request)
        if organization is None and owner is None:
            return Response({"detail": "Not a member of that organization."}, status=status.HTTP_403_FORBIDDEN)
        if organization is not None and get_member_role(request.user, organization) not in {"owner", "admin"}:
            return Response({"detail": "Only the owner or an admin can manage billing."}, status=status.HTTP_403_FORBIDDEN)

        plan = Plan.objects.filter(id=data["plan_id"], is_active=True).first()
        if not plan:
            return Response({"detail": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

        subscription = get_or_create_default_subscription(organization=organization, owner=owner)
        subscription.plan = plan
        subscription.save(update_fields=["plan"])

        result = start_checkout(subscription=subscription, provider_name=data["provider"])

        log_audit_event(
            actor=request.user, organization=organization, action="billing.checkout_started",
            resource_type="subscription", resource_id=subscription.id, request=request,
            metadata={"plan": plan.slug, "provider": data["provider"]},
        )
        return Response(
            {"redirect_url": result.redirect_url, "provider_reference": result.provider_reference},
            status=status.HTTP_201_CREATED,
        )


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=SubscriptionSerializer)
    def post(self, request):
        organization, owner = resolve_tenant(request)
        if organization is not None and get_member_role(request.user, organization) not in {"owner", "admin"}:
            return Response({"detail": "Only the owner or an admin can manage billing."}, status=status.HTTP_403_FORBIDDEN)

        subscription = get_or_create_default_subscription(organization=organization, owner=owner)
        subscription.cancel_at_period_end = True
        subscription.save(update_fields=["cancel_at_period_end"])

        log_audit_event(
            actor=request.user, organization=organization, action="billing.subscription_cancelled",
            resource_type="subscription", resource_id=subscription.id, request=request,
        )
        return Response(SubscriptionSerializer(subscription).data)


class ReactivateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=SubscriptionSerializer)
    def post(self, request):
        organization, owner = resolve_tenant(request)
        if organization is not None and get_member_role(request.user, organization) not in {"owner", "admin"}:
            return Response({"detail": "Only the owner or an admin can manage billing."}, status=status.HTTP_403_FORBIDDEN)

        subscription = get_or_create_default_subscription(organization=organization, owner=owner)
        subscription.cancel_at_period_end = False
        if subscription.status == SubscriptionStatus.CANCELLED:
            subscription.status = SubscriptionStatus.ACTIVE
        subscription.save(update_fields=["cancel_at_period_end", "status"])
        return Response(SubscriptionSerializer(subscription).data)


class InvoiceListView(ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        organization, owner = resolve_tenant(self.request)
        qs = Payment.objects.all()
        if organization is not None:
            return qs.filter(organization=organization)
        return qs.filter(owner=owner, organization__isnull=True)
