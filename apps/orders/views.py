from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsPlatformStaff
from apps.core.permissions import get_active_memberships, get_member_role
from apps.core.utils import log_audit_event
from apps.organizations.models import Organization
from apps.orders.models import Order, PhysicalCardProduct
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
    PhysicalCardProductSerializer,
)
from apps.orders.services import OrderValidationError, advance_status, create_order


class PhysicalCardProductListView(ListAPIView):
    serializer_class = PhysicalCardProductSerializer
    permission_classes = [AllowAny]
    queryset = PhysicalCardProduct.objects.filter(is_active=True)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["status", "payment_status"]

    def get_queryset(self):
        user = self.request.user
        if user.is_platform_staff:
            return Order.objects.all()
        org_ids = [m.organization_id for m in get_active_memberships(user)]
        return Order.objects.filter(Q(customer=user) | Q(organization_id__in=org_ids)).distinct()

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization = None
        if data.get("organization_id"):
            organization = Organization.objects.filter(id=data["organization_id"]).first()
            if not organization or get_member_role(request.user, organization) not in {"owner", "admin"}:
                return Response({"detail": "You do not have permission to order for this organization."}, status=status.HTTP_403_FORBIDDEN)

        try:
            order = create_order(
                customer=request.user, organization=organization,
                items_data=data["items"], shipping_address_data=data["shipping_address"],
            )
        except OrderValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from apps.billing.services import start_order_checkout

        result = start_order_checkout(order=order, provider_name=data["provider"])

        log_audit_event(
            actor=request.user, organization=organization, action="order.created",
            resource_type="order", resource_id=order.id, request=request,
        )
        return Response(
            {"order": OrderSerializer(order).data, "redirect_url": result.redirect_url},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsPlatformStaff])
    def status_update(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        advance_status(
            order, data["status"],
            description=data.get("description", ""), tracking_number=data.get("tracking_number", ""),
        )
        log_audit_event(
            actor=request.user, organization=order.organization, action="order.status_updated",
            resource_type="order", resource_id=order.id, request=request, metadata={"status": data["status"]},
        )
        return Response(OrderSerializer(order).data)
