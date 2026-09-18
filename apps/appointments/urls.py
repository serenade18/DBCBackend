from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.appointments.views import (
    AppointmentServiceDetailView,
    AppointmentServiceListCreateView,
    AppointmentViewSet,
    AvailabilityRuleDetailView,
    AvailabilityRuleListCreateView,
    PublicAvailabilityView,
    PublicBookingView,
)

router = DefaultRouter()
router.register("", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("vcards/<uuid:vcard_id>/services/", AppointmentServiceListCreateView.as_view(), name="appointment-service-list"),
    path("services/<uuid:pk>/", AppointmentServiceDetailView.as_view(), name="appointment-service-detail"),

    path("vcards/<uuid:vcard_id>/availability/", AvailabilityRuleListCreateView.as_view(), name="availability-rule-list"),
    path("availability/<uuid:pk>/", AvailabilityRuleDetailView.as_view(), name="availability-rule-detail"),

    path("public/<slug:vcard_slug>/availability/", PublicAvailabilityView.as_view(), name="public-availability"),
    path("public/<slug:vcard_slug>/book/", PublicBookingView.as_view(), name="public-booking"),
] + router.urls
