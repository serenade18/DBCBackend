import base64
import logging
from datetime import datetime

import requests
from django.conf import settings

from apps.billing.providers.base import CheckoutResult, PaymentProvider

logger = logging.getLogger("django")

SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"


class MpesaProvider(PaymentProvider):
    """
    M-Pesa (Safaricom Daraja) STK Push. Unlike Stripe, Daraja has no native
    recurring-subscription concept, so `create_subscription` triggers a
    single STK push for one billing period; period renewal is driven by the
    subscription-check Celery beat task re-prompting for payment near
    `current_period_end` (see apps.billing.tasks.check_subscriptions).
    """

    name = "mpesa"

    @property
    def base_url(self) -> str:
        return PRODUCTION_BASE_URL if settings.MPESA_ENV == "production" else SANDBOX_BASE_URL

    def _access_token(self) -> str:
        credentials = base64.b64encode(
            f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
        ).decode()
        response = requests.get(
            f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def create_customer(self, user) -> str:
        # Daraja has no customer object; the phone number *is* the identity.
        return user.phone or ""

    def create_subscription(self, subscription) -> CheckoutResult:
        tenant = subscription.organization or subscription.owner
        phone = getattr(tenant, "phone", "") or getattr(subscription.owner, "phone", "")
        amount = subscription.plan.monthly_price

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
        ).decode()

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": f"{settings.PUBLIC_BASE_URL}/api/v1/webhooks/mpesa/",
            "AccountReference": str(subscription.id),
            "TransactionDesc": f"{subscription.plan.name} subscription",
        }
        response = requests.post(
            f"{self.base_url}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {self._access_token()}"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return CheckoutResult(provider_reference=data.get("CheckoutRequestID", ""), raw=data)

    def cancel_subscription(self, subscription) -> None:
        # No recurring mandate to cancel on Daraja's side — local status
        # change (in services.py) is sufficient; renewal simply stops being
        # prompted.
        return None

    def verify_payment(self, payload: dict) -> bool:
        stk_callback = payload.get("Body", {}).get("stkCallback", {})
        return stk_callback.get("ResultCode") == 0

    def handle_webhook(self, payload: dict, headers: dict) -> None:
        stk_callback = payload.get("Body", {}).get("stkCallback", {})
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        logger.info("M-Pesa callback received: checkout=%s result=%s", checkout_request_id, result_code)

        metadata_items = {
            item["Name"]: item.get("Value")
            for item in stk_callback.get("CallbackMetadata", {}).get("Item", [])
        }

        from apps.billing.services import apply_provider_event

        apply_provider_event(
            provider=self.name,
            event_type="payment.successful" if result_code == 0 else "payment.failed",
            data={
                "provider_reference": checkout_request_id,
                "amount": metadata_items.get("Amount"),
                "receipt": metadata_items.get("MpesaReceiptNumber"),
                "phone": metadata_items.get("PhoneNumber"),
            },
        )
