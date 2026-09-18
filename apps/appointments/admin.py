from django.contrib import admin

from apps.appointments.models import Appointment, AppointmentService, AvailabilityRule


@admin.register(AppointmentService)
class AppointmentServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "vcard", "duration_minutes", "price", "is_active"]


@admin.register(AvailabilityRule)
class AvailabilityRuleAdmin(admin.ModelAdmin):
    list_display = ["vcard", "weekday", "start_time", "end_time", "timezone"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["customer_name", "vcard", "service", "date", "start_time", "status"]
    list_filter = ["status", "date"]
    search_fields = ["customer_name", "customer_email", "vcard__slug"]
