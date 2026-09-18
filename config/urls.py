from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Health checks (unauthenticated)
    path("health/", include("apps.core.urls")),

    # API schema / docs
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),

    # Versioned API — dashboard/authenticated surface
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/organizations/", include("apps.organizations.urls")),
    path("api/v1/vcards/", include("apps.cards.urls")),
    path("api/v1/", include("apps.profile_blocks.urls")),
    path("api/v1/templates/", include("apps.templates.urls")),
    path("api/v1/appointments/", include("apps.appointments.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/nfc/", include("apps.nfc_qr.urls")),
    path("api/v1/enquiries/", include("apps.enquiries.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/directory/", include("apps.directory.urls")),

    # Payment provider webhooks (unauthenticated, signature-verified)
    path("api/v1/webhooks/", include("apps.billing.webhook_urls")),

    # Public, unauthenticated surfaces
    path("directory/", include("apps.directory.public_urls")),
    path("", include("apps.cards.public_urls")),  # /@<slug>/, /c/<slug>/, .vcf, QR
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
