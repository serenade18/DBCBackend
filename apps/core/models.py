import uuid

from django.db import models


class UUIDModel(models.Model):
    """Abstract base: UUID primary key, per spec's "use UUID primary keys"."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    class Meta:
        abstract = True


class OrderedVisibleModel(models.Model):
    """Shared by the small content models (links, gallery items, services, ...)."""

    position = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["position", "created_at"]


class AuditLog(BaseModel):
    """
    Immutable record of significant actions across the platform (§42).
    Written explicitly by views/services via apps.core.utils.log_audit_event
    rather than inferred from generic request middleware, since the actions
    worth tracking (card published, member invited, payment received, ...)
    are semantic events, not raw HTTP verbs.
    """

    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        return f"{self.action} on {self.resource_type}:{self.resource_id}"
