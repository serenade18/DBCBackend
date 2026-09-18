import logging

import requests
from django.conf import settings

from apps.billing.providers.base import CheckoutResult, PaymentProvider

logger = logging.getLogger("django")

BASE_URL = "https://api.sasapay.app/api/v1"


class SasaPayProvider(PaymentProvider):
    """
    SasaPay checkout — same one-off-charge-per-period pattern as MpesaProvider
    (see its docstring); SasaPay also has no native recurring subscription API.
    """

    name = "sasapay"

    def _access_token(self) -> str:
        response = requests.post(
            f"{BASE_URL}/auth/token/",
            data={
                "client_id": settings.SASAPAY_CLIENT_ID,
                "client_secret": settings.SASAPAY_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def create_customer(self, user) -> str:
        return user.phone or ""

    def create_subscription(self, subscription) -> CheckoutResult:
        tenant = subscription.organization or subscription.owner
        phone = getattr(tenant, "phone", "") or getattr(subscription.owner, "phone", "")
        return self.create_charge(
            amount=subscription.plan.monthly_price,
            currency=subscription.plan.currency,
            reference=str(subscription.id),
            description=f"{subscription.plan.name} subscription",
            phone=phone,
        )

    def cancel_subscription(self, subscription) -> None:
        return None

    def create_charge(self, *, amount, currency, reference, description, phone="", customer_id="") -> CheckoutResult:
        payload = {
            "MerchantCode": settings.SASAPAY_CLIENT_ID,
            "NetworkCode": "63902",
            "PhoneNumber": phone,
            "TransactionDesc": description,
            "Amount": str(amount),
            "Currency": currency,
            "CallBackURL": f"{settings.PUBLIC_BASE_URL}/api/v1/webhooks/sasapay/",
            "AccountReference": reference,
        }
        response = requests.post(
            f"{BASE_URL}/payments/checkout/",
            json=payload,
            headers={"Authorization": f"Bearer {self._access_token()}"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return CheckoutResult(provider_reference=data.get("CheckoutRequestID", data.get("MerchantRequestID", "")), raw=data)

    def verify_payment(self, payload: dict) -> bool:
        return str(payload.get("ResultCode")) == "0"

    def handle_webhook(self, payload: dict, headers: dict) -> None:
        logger.info("SasaPay callback received: %s", payload.get("CheckoutRequestID"))

        from apps.billing.services import apply_provider_event

        apply_provider_event(
            provider=self.name,
            event_type="payment.successful" if str(payload.get("ResultCode")) == "0" else "payment.failed",
            data={
                "provider_reference": payload.get("CheckoutRequestID"),
                "amount": payload.get("Amount"),
                "receipt": payload.get("TransactionReceipt"),
                "phone": payload.get("PhoneNumber"),
            },
        )
