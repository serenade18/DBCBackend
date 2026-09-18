from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CheckoutResult:
    provider_reference: str
    redirect_url: str | None = None
    raw: dict | None = None


class PaymentProvider(ABC):
    """
    Common interface every payment provider must implement (§30). Keeps
    subscription/order code decoupled from any one provider's SDK — new
    providers are added by subclassing this, never by branching on
    `provider == "stripe"` throughout the app.
    """

    name: str

    @abstractmethod
    def create_customer(self, user) -> str:
        """Returns a provider-side customer id."""

    @abstractmethod
    def create_subscription(self, subscription) -> CheckoutResult:
        """Starts/links a subscription on the provider's side."""

    @abstractmethod
    def cancel_subscription(self, subscription) -> None:
        ...

    @abstractmethod
    def verify_payment(self, payload: dict) -> bool:
        """Verifies a payment payload/signature came from this provider."""

    @abstractmethod
    def handle_webhook(self, payload: dict, headers: dict) -> None:
        """Processes a verified webhook payload (idempotent)."""
