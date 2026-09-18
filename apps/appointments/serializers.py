from rest_framework import serializers

from apps.appointments.models import Appointment, AppointmentService, AvailabilityRule


class AppointmentServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentService
        fields = ["id", "vcard", "name", "description", "duration_minutes", "price", "currency", "is_active"]
        read_only_fields = ["id", "vcard"]


class AvailabilityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityRule
        fields = ["id", "vcard", "weekday", "start_time", "end_time", "timezone"]
        read_only_fields = ["id", "vcard"]


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "id", "vcard", "service", "customer_name", "customer_email", "customer_phone",
            "date", "start_time", "end_time", "status", "notes", "created_at",
        ]
        read_only_fields = ["id", "vcard", "end_time", "created_at"]


class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["status", "notes"]


class PublicBookingSerializer(serializers.Serializer):
    service_id = serializers.UUIDField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    customer_name = serializers.CharField(max_length=255)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
