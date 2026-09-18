from django.urls import path

from apps.core.views import DatabaseHealthView, HealthView, RedisHealthView

urlpatterns = [
    path("", HealthView.as_view(), name="health"),
    path("db/", DatabaseHealthView.as_view(), name="health-db"),
    path("redis/", RedisHealthView.as_view(), name="health-redis"),
]
