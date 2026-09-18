from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.enquiries.views import EnquiryViewSet, PublicEnquirySubmitView

router = DefaultRouter()
router.register("", EnquiryViewSet, basename="enquiry")

urlpatterns = [
    path("submit/<slug:vcard_slug>/", PublicEnquirySubmitView.as_view(), name="enquiry-submit"),
] + router.urls
