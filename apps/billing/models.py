from django.db import models

from apps.core.models import BaseModel


class Plan(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")

    max_vcards = models.PositiveIntegerField(default=1)
    max_storage_mb = models.PositiveIntegerField(default=100)
    max_team_members = models.PositiveIntegerField(default=1)
    max_gallery_items = models.PositiveIntegerField(default=5)
    max_products = models.PositiveIntegerField(default=5)
    max_services = models.PositiveIntegerField(default=5)

    analytics_enabled = models.BooleanField(default=False)
    appointments_enabled = models.BooleanField(default=False)
    custom_domain_enabled = models.BooleanField(default=False)
    directory_enabled = models.BooleanField(default=True)
    remove_branding = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["monthly_price"]

    def __str__(self):
        return self.name

    def feature_map(self) -> dict:
        return {
            "analytics": self.analytics_enabled,
            "appointments": self.appointments_enabled,
            "custom_domain": self.custom_domain_enabled,
            "directory": self.directory_enabled,
            "remove_branding": self.remove_branding,
            "priority_support": self.priority_support,
        }


class SubscriptionProvider(models.TextChoices):
    STRIPE = "stripe", "Stripe"
    MPESA = "mpesa", "M-Pesa"
    SASAPAY = "sasapay", "SasaPay"
    NONE = "none", "None (free plan)"


class SubscriptionStatus(models.TextChoices):
    TRIALING = "trialing", "Trialing"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past due"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"
    PAUSED = "paused", "Paused"


class Subscription(BaseModel):
    """
    Billed to either an Organization or, for individual users who never
    formalize an organization (§4), directly to a User. Exactly one of
    `organization` / `owner` is set — see clean().
    """

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="subscriptions",
        null=True, blank=True,
    )
    owner = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="personal_subscriptions",
        null=True, blank=True,
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    provider = models.CharField(max_length=20, choices=SubscriptionProvider.choices, default=SubscriptionProvider.NONE)
    provider_subscription_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.TRIALING)

    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(organization__isnull=False, owner__isnull=True)
                    | models.Q(organization__isnull=True, owner__isnull=False)
                ),
                name="subscription_belongs_to_org_xor_user",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["owner", "status"]),
        ]

    def __str__(self):
        tenant = self.organization or self.owner
        return f"{tenant} -> {self.plan.name} ({self.status})"

    @property
    def is_usable(self) -> bool:
        return self.status in {SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SUCCESSFUL = "successful", "Successful"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class Payment(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.SET_NULL, related_name="payments", null=True, blank=True
    )
    owner = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="personal_payments", null=True, blank=True
    )
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, related_name="payments", null=True, blank=True)
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, related_name="payments", null=True, blank=True)
    provider = models.CharField(max_length=20, choices=SubscriptionProvider.choices)
    provider_reference = models.CharField(max_length=255, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=255, blank=True, unique=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_method = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["provider", "provider_reference"]),
        ]

    def __str__(self):
        return f"{self.amount} {self.currency} ({self.status})"
