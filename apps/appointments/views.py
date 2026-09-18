from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.appointments.models import Appointment, AppointmentService, AvailabilityRule
from apps.appointments.serializers import (
    AppointmentSerializer,
    AppointmentServiceSerializer,
    AppointmentStatusUpdateSerializer,
    AvailabilityRuleSerializer,
    PublicBookingSerializer,
)
from apps.appointments.services import SlotUnavailableError, book_appointment, get_available_slots
from apps.cards.models import VCard
from apps.cards.services import accessible_vcard_ids, can_manage_vcard
from apps.profile_blocks.views import VCardScopedDetailView, VCardScopedListCreateView


class AppointmentServiceListCreateView(VCardScopedListCreateView):
    model = AppointmentService
    related_name = "appointment_services"
    serializer_class = AppointmentServiceSerializer


class AppointmentServiceDetailView(VCardScopedDetailView):
    model = AppointmentService
    serializer_class = AppointmentServiceSerializer


class AvailabilityRuleListCreateView(VCardScopedListCreateView):
    model = AvailabilityRule
    related_name = "availability_rules"
    serializer_class = AvailabilityRuleSerializer


class AvailabilityRuleDetailView(VCardScopedDetailView):
    model = AvailabilityRule
    serializer_class = AvailabilityRuleSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return AppointmentStatusUpdateSerializer
        return AppointmentSerializer

    def get_queryset(self):
        return Appointment.objects.filter(vcard_id__in=accessible_vcard_ids(self.request.user))

    def get_object(self):
        obj = super().get_object()
        if not can_manage_vcard(self.request.user, obj.vcard):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to manage appointments for this card.")
        return obj


class PublicAvailabilityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public-card"

    def get(self, request, vcard_slug):
        vcard = get_object_or_404(VCard, slug=vcard_slug)
        service_id = request.query_params.get("service_id")
        date_str = request.query_params.get("date")
        if not (service_id and date_str):
            return Response({"detail": "service_id and date are required."}, status=status.HTTP_400_BAD_REQUEST)

        service = get_object_or_404(AppointmentService, id=service_id, vcard=vcard, is_active=True)
        from datetime import date as date_cls

        try:
            date = date_cls.fromisoformat(date_str)
        except ValueError:
            return Response({"detail": "Invalid date."}, status=status.HTTP_400_BAD_REQUEST)

        slots = get_available_slots(vcard, service, date)
        return Response({"slots": [{"start_time": s.isoformat(), "end_time": e.isoformat()} for s, e in slots]})


class PublicBookingView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "enquiry-submit"

    def post(self, request, vcard_slug):
        vcard = get_object_or_404(VCard, slug=vcard_slug)
        if not vcard.is_publicly_viewable:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PublicBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = get_object_or_404(AppointmentService, id=data["service_id"], vcard=vcard, is_active=True)

        try:
            appointment = book_appointment(
                vcard=vcard, service=service, customer_name=data["customer_name"],
                customer_email=data["customer_email"], customer_phone=data.get("customer_phone", ""),
                date=data["date"], start_time=data["start_time"], notes=data.get("notes", ""),
            )
        except SlotUnavailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)
