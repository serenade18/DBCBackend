import logging

import requests
from django.conf import settings

logger = logging.getLogger("django")


def send_sms(*, to: str, message: str) -> bool:
    """
    Generic SMS sender. No specific provider is mandated by the spec beyond
    SMS_API_KEY, so this posts to a configurable HTTP gateway and no-ops
    (logs only) when no key is configured — swap the body for the chosen
    provider's SDK/API (e.g. Africa's Talking, Twilio) when one is picked.
    """
    if not settings.SMS_API_KEY:
        logger.info("SMS_API_KEY not configured; skipping SMS to %s: %s", to, message)
        return False

    try:
        response = requests.post(
            "https://api.sms-provider.example.com/v1/send",
            json={"to": to, "message": message, "sender_id": settings.SMS_SENDER_ID},
            headers={"Authorization": f"Bearer {settings.SMS_API_KEY}"},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Failed to send SMS to %s", to)
        return False
