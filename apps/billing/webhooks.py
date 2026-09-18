import json
import logging

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.providers.mpesa import MpesaProvider
from apps.billing.providers.sasapay import SasaPayProvider
from apps.billing.providers.stripe import StripeProvider

logger = logging.getLogger("django")


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "webhook"

    def post(self, request):
        import stripe

        try:
            event = StripeProvider.construct_event(request)
        except (ValueError, stripe.error.SignatureVerificationError):
            logger.warning("Rejected Stripe webhook: invalid signature/payload")
            return Response(status=400)

        StripeProvider().handle_webhook(event, dict(request.headers))
        return Response(status=200)


class MpesaWebhookView(APIView):
    """
    Daraja does not sign callbacks; it authenticates by calling a URL only
    Safaricom's servers know (kept secret / IP-allowlisted at the infra
    layer). No shared-secret signature scheme exists to verify here.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "webhook"

    def post(self, request):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response(status=400)

        MpesaProvider().handle_webhook(payload, dict(request.headers))
        return Response({"ResultCode": 0, "ResultDesc": "Accepted"}, status=200)


class SasaPayWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "webhook"

    def post(self, request):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response(status=400)

        SasaPayProvider().handle_webhook(payload, dict(request.headers))
        return Response({"ResultCode": 0, "ResultDesc": "Accepted"}, status=200)
