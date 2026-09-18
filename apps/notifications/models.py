from django.db import models

from apps.core.models import BaseModel


class NotificationType(models.TextChoices):
    WELCOME = "welcome", "Welcome"
    EMAIL_VERIFICATION = "email_verification", "Email verification"
    PASSWORD_RESET = "password_reset", "Password reset"
    NEW_ENQUIRY = "new_enquiry", "New enquiry"
    NEW_APPOINTMENT = "new_appointment", "New appointment"
    APPOINTMENT_REMINDER = "appointment_reminder", "Appointment reminder"
    PAYMENT_SUCCESSFUL = "payment_successful", "Payment successful"
    PAYMENT_FAILED = "payment_failed", "Payment failed"
    SUBSCRIPTION_EXPIRING = "subscription_expiring", "Subscription expiring"
    ORDER_RECEIVED = "order_received", "Order received"
    ORDER_SHIPPED = "order_shipped", "Order shipped"
    ORDER_DELIVERED = "order_delivered", "Order delivered"
    TEAM_INVITATION = "team_invitation", "Team invitation"


class Notification(BaseModel):
    """In-app notification feed entry (§43)."""

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=32, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    link_url = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "created_at"])]

    def __str__(self):
        return f"{self.type} -> {self.user_id}"
