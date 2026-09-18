from django.db import models

from apps.core.models import BaseModel


class AppointmentService(BaseModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="appointment_services")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class AvailabilityRule(BaseModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="availability_rules")
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=64, default="UTC")

    class Meta:
        ordering = ["weekday", "start_time"]
        indexes = [models.Index(fields=["vcard", "weekday"])]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time}-{self.end_time}"


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"
    NO_SHOW = "no_show", "No show"


class Appointment(BaseModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(AppointmentService, on_delete=models.CASCADE, related_name="appointments")
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=32, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.PENDING)
    notes = models.TextField(blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date", "-start_time"]
        indexes = [
            models.Index(fields=["vcard", "date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.customer_name} @ {self.date} {self.start_time}"
