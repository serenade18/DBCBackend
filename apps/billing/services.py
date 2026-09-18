import logging

from django.db.models import Q
from django.utils import timezone

from apps.billing.models import (
    Payment,
    PaymentStatus,
    Plan,
    Subscription,
    SubscriptionProvider,
    SubscriptionStatus,
)
from apps.billing.providers.base import PaymentProvider

logger = logging.getLogger("django")

TRIAL_DAYS = 14
DEFAULT_FREE_PLAN_SLUG = "free"


def get_provider(name: str) -> PaymentProvider:
    if name == SubscriptionProvider.STRIPE:
        from apps.billing.providers.stripe import StripeProvider

        return StripeProvider()
    if name == SubscriptionProvider.MPESA:
        from apps.billing.providers.mpesa import MpesaProvider

        return MpesaProvider()
    if name == SubscriptionProvider.SASAPAY:
        from apps.billing.providers.sasapay import SasaPayProvider

        return SasaPayProvider()
    raise ValueError(f"Unknown payment provider: {name}")


def get_active_subscription(*, organization=None, owner=None) -> Subscription | None:
    qs = Subscription.objects.filter(status__in=[
        SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE, SubscriptionStatus.PAUSED,
    ])
    if organization is not None:
        qs = qs.filter(organization=organization)
    else:
        qs = qs.filter(owner=owner)
    return qs.order_by("-created_at").first()


def get_or_create_default_subscription(*, organization=None, owner=None) -> Subscription:
    """Every organization/individual gets an implicit trial-on-Free-plan
    subscription so entitlement checks always have a baseline (§27, §29)."""
    existing = get_active_subscription(organization=organization, owner=owner)
    if existing:
        return existing

    plan, _ = Plan.objects.get_or_create(
        slug=DEFAULT_FREE_PLAN_SLUG,
        defaults={"name": "Free", "monthly_price": 0, "annual_price": 0, "max_vcards": 1},
    )
    now = timezone.now()
    return Subscription.objects.create(
        organization=organization,
        owner=owner,
        plan=plan,
        provider=SubscriptionProvider.NONE,
        status=SubscriptionStatus.TRIALING,
        trial_start=now,
        trial_end=now + timezone.timedelta(days=TRIAL_DAYS),
        current_period_start=now,
        current_period_end=now + timezone.timedelta(days=TRIAL_DAYS),
    )


def start_checkout(*, subscription: Subscription, provider_name: str):
    provider = get_provider(provider_name)
    tenant_user = subscription.owner or (subscription.organization and _org_owner_user(subscription.organization))
    if tenant_user:
        provider.create_customer(tenant_user)

    result = provider.create_subscription(subscription)

    subscription.provider = provider_name
    subscription.provider_subscription_id = result.provider_reference
    subscription.save(update_fields=["provider", "provider_subscription_id"])

    Payment.objects.create(
        organization=subscription.organization,
        owner=subscription.owner,
        subscription=subscription,
        provider=provider_name,
        provider_reference=result.provider_reference,
        amount=subscription.plan.monthly_price,
        currency=subscription.plan.currency,
        status=PaymentStatus.PENDING,
    )
    return result


def start_order_checkout(*, order, provider_name: str):
    """One-off charge checkout for a physical card Order (§32), as opposed
    to the recurring subscription flow in start_checkout()."""
    provider = get_provider(provider_name)
    tenant_user = order.customer
    phone = getattr(tenant_user, "phone", "") if tenant_user else ""

    result = provider.create_charge(
        amount=order.total, currency=order.currency, reference=str(order.id),
        description=f"Order {order.order_number}", phone=phone,
    )

    Payment.objects.create(
        organization=order.organization,
        owner=order.customer if not order.organization else None,
        order=order,
        provider=provider_name,
        provider_reference=result.provider_reference,
        amount=order.total,
        currency=order.currency,
        status=PaymentStatus.PENDING,
    )
    return result


def apply_provider_event(*, provider: str, event_type: str, data: dict):
    """Idempotently reconciles a verified webhook event into Payment /
    Subscription state (§31: 'all provider callbacks must be idempotent')."""
    reference = data.get("provider_reference") or data.get("id") or data.get("CheckoutRequestID")
    payment = Payment.objects.filter(provider=provider, provider_reference=reference).select_related("subscription", "order").first()

    success_events = {"payment.successful", "checkout.session.completed", "invoice.paid", "invoice_payment.paid"}
    failure_events = {"payment.failed", "invoice.payment_failed"}

    if event_type in success_events:
        if payment is None:
            logger.warning("Webhook %s/%s: no matching Payment for reference %s", provider, event_type, reference)
            return
        if payment.status == PaymentStatus.SUCCESSFUL:
            return  # already processed — idempotent no-op
        payment.status = PaymentStatus.SUCCESSFUL
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])

        if payment.subscription:
            _activate_period(payment.subscription)
        if payment.order:
            _mark_order_paid(payment.order)
        _notify_payment(payment, success=True)

    elif event_type in failure_events:
        if payment is None:
            return
        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=["status"])
        if payment.subscription:
            payment.subscription.status = SubscriptionStatus.PAST_DUE
            payment.subscription.save(update_fields=["status"])
        _notify_payment(payment, success=False)


def _mark_order_paid(order):
    from apps.orders.models import OrderStatus, PaymentStatus as OrderPaymentStatus

    if order.payment_status == OrderPaymentStatus.PAID:
        return  # idempotent no-op
    order.payment_status = OrderPaymentStatus.PAID
    order.status = OrderStatus.PAID
    order.save(update_fields=["payment_status", "status"])
    order.shipping_events.create(status=OrderStatus.PAID, description="Payment received.")


def _activate_period(subscription: Subscription, period_days: int = 30):
    now = timezone.now()
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.current_period_start = now
    subscription.current_period_end = now + timezone.timedelta(days=period_days)
    subscription.save(update_fields=["status", "current_period_start", "current_period_end"])


def _notify_payment(payment: Payment, success: bool):
    from apps.notifications.tasks import notify_in_app_task

    user = payment.owner or _org_owner_user(payment.organization) if payment.organization else payment.owner
    if not user:
        return
    notify_in_app_task.delay(
        str(user.id),
        "payment_successful" if success else "payment_failed",
        "Payment received" if success else "Payment failed",
        f"{payment.amount} {payment.currency}",
    )


def _org_owner_user(organization):
    from apps.organizations.models import OrganizationRole

    membership = organization.members.filter(role=OrganizationRole.OWNER, status="active").select_related("user").first()
    return membership.user if membership else None


class EntitlementService:
    """Central feature-gating entry point (§29):

        EntitlementService(organization).can("analytics")
        EntitlementService(user).can_create_vcard()
    """

    def __init__(self, tenant):
        from apps.accounts.models import User
        from apps.organizations.models import Organization

        if isinstance(tenant, Organization):
            self.organization, self.owner = tenant, None
        elif isinstance(tenant, User):
            self.organization, self.owner = None, tenant
        else:
            raise TypeError("EntitlementService expects an Organization or User instance")

    @property
    def subscription(self) -> Subscription:
        return get_or_create_default_subscription(organization=self.organization, owner=self.owner)

    @property
    def plan(self) -> Plan:
        return self.subscription.plan

    def can(self, feature: str) -> bool:
        if not self.subscription.is_usable:
            return False
        return bool(self.plan.feature_map().get(feature, False))

    def can_create_vcard(self, current_count: int | None = None) -> bool:
        if not self.subscription.is_usable:
            return False
        if current_count is None:
            current_count = self._current_vcard_count()
        return current_count < self.plan.max_vcards

    def can_add_team_member(self, current_count: int) -> bool:
        if not self.subscription.is_usable:
            return False
        return current_count < self.plan.max_team_members

    def can_upload(self, size_bytes: int) -> bool:
        """
        TODO: wire real aggregate storage accounting (e.g. a running
        per-tenant byte counter updated on upload/delete) once media
        volume matters. For now this only rejects single files larger
        than the plan's whole quota, rather than tracking cumulative use.
        """
        if not self.subscription.is_usable:
            return False
        size_mb = size_bytes / (1024 * 1024)
        return size_mb <= self.plan.max_storage_mb

    def can_add_gallery_item(self, current_count: int) -> bool:
        return current_count < self.plan.max_gallery_items

    def can_add_product(self, current_count: int) -> bool:
        return current_count < self.plan.max_products

    def can_add_service(self, current_count: int) -> bool:
        return current_count < self.plan.max_services

    def _current_vcard_count(self) -> int:
        from apps.cards.models import VCard

        qs = VCard.objects.exclude(status="archived")
        if self.organization:
            return qs.filter(organization=self.organization).count()
        return qs.filter(organization__isnull=True, owner=self.owner).count()
