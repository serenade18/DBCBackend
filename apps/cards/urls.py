from rest_framework.routers import DefaultRouter

from apps.cards.views import VCardViewSet

router = DefaultRouter()
router.register("", VCardViewSet, basename="vcard")

urlpatterns = router.urls
