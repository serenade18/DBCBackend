from rest_framework.routers import DefaultRouter

from apps.nfc_qr.views import NfcCardViewSet

router = DefaultRouter()
router.register("", NfcCardViewSet, basename="nfc-card")

urlpatterns = router.urls
