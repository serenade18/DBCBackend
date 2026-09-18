import logging

from rest_framework.views import exception_handler

logger = logging.getLogger("django")


class EntitlementError(Exception):
    """Raised when a subscription's plan limits block an action (§29)."""

    def __init__(self, message: str, code: str = "entitlement_limit_reached"):
        self.message = message
        self.code = code
        super().__init__(message)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, EntitlementError):
        from rest_framework import status
        from rest_framework.response import Response

        return Response(
            {"detail": exc.message, "code": exc.code},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )

    if response is not None:
        response.data = {"detail": response.data} if isinstance(response.data, str) else response.data
    else:
        logger.exception("Unhandled exception", exc_info=exc)

    return response
