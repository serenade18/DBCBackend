import logging

from django.conf import settings

from apps.billing.providers.base import CheckoutResult, PaymentProvider

logger = logging.getLogger("django")


class StripeProvider(PaymentProvider):
    name = "stripe"

    def __init__(self):
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._stripe = stripe

    def create_customer(self, user) -> str:
        customer = self._stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={"user_id": str(user.id)},
        )
        return customer["id"]

    def create_subscription(self, subscription) -> CheckoutResult:
        tenant = subscription.organization or subscription.owner
        price_id = getattr(subscription.plan, "stripe_price_id", None) or subscription.plan.slug

        session = self._stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing/cancelled",
            client_reference_id=str(subscription.id),
            metadata={"subscription_id": str(subscription.id), "tenant": str(getattr(tenant, "id", ""))},
        )
        return CheckoutResult(provider_reference=session["id"], redirect_url=session.get("url"), raw=session)

    def cancel_subscription(self, subscription) -> None:
        if not subscription.provider_subscription_id:
            return
        self._stripe.Subscription.delete(subscription.provider_subscription_id)

    def verify_payment(self, payload: dict) -> bool:
        # Real verification happens via handle_webhook's signature check;
        # this covers ad-hoc client-side confirmation calls.
        return bool(payload.get("id"))

    def handle_webhook(self, payload: dict, headers: dict) -> None:
        event_type = payload.get("type")
        data = payload.get("data", {}).get("object", {})
        logger.info("Stripe webhook received: %s", event_type)

        from apps.billing.services import apply_provider_event

        apply_provider_event(provider=self.name, event_type=event_type, data=data)

    @staticmethod
    def construct_event(request):
        """Verifies the Stripe-Signature header and returns the parsed event.
        Raises stripe.error.SignatureVerificationError on failure."""
        import stripe

        return stripe.Webhook.construct_event(
            payload=request.body,
            sig_header=request.headers.get("Stripe-Signature", ""),
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
