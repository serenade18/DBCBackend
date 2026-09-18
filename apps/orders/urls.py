from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.orders.views import OrderViewSet, PhysicalCardProductListView

router = DefaultRouter()
router.register("", OrderViewSet, basename="order")

urlpatterns = [
    path("products/", PhysicalCardProductListView.as_view(), name="physical-card-product-list"),
] + router.urls
