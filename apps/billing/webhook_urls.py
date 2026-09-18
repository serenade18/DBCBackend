from django.urls import path

from apps.billing.webhooks import MpesaWebhookView, SasaPayWebhookView, StripeWebhookView

urlpatterns = [
    path("stripe/", StripeWebhookView.as_view(), name="webhook-stripe"),
    path("mpesa/", MpesaWebhookView.as_view(), name="webhook-mpesa"),
    path("sasapay/", SasaPayWebhookView.as_view(), name="webhook-sasapay"),
]
