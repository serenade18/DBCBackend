from rest_framework.routers import DefaultRouter

from apps.templates.views import CardTemplateViewSet

router = DefaultRouter()
router.register("", CardTemplateViewSet, basename="template")

urlpatterns = router.urls
