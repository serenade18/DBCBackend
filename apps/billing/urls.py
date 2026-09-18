from django.urls import path

from apps.billing.views import (
    CancelSubscriptionView,
    CheckoutView,
    InvoiceListView,
    PlanListView,
    ReactivateSubscriptionView,
    SubscriptionView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="billing-plans"),
    path("subscription/", SubscriptionView.as_view(), name="billing-subscription"),
    path("checkout/", CheckoutView.as_view(), name="billing-checkout"),
    path("cancel/", CancelSubscriptionView.as_view(), name="billing-cancel"),
    path("reactivate/", ReactivateSubscriptionView.as_view(), name="billing-reactivate"),
    path("invoices/", InvoiceListView.as_view(), name="billing-invoices"),
]
