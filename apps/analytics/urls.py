from django.urls import path

from apps.analytics.views import VCardAnalyticsView

urlpatterns = [
    path("", VCardAnalyticsView.as_view(), name="analytics"),
]
