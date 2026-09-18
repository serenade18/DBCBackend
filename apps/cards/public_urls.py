from django.urls import path

from apps.cards.public_views import (
    PublicVCardAnalyticsView,
    PublicVCardDetailView,
    public_qr_download,
    public_vcf_download,
    render_public_card,
    track_link_click,
)

urlpatterns = [
    path("@<slug:slug>/", render_public_card, name="public-vcard"),
    path("c/<slug:slug>/", render_public_card, name="public-vcard-alias"),

    path("@<slug:slug>/contact/", public_vcf_download, name="public-vcard-contact"),
    path("c/<slug:slug>/contact/", public_vcf_download, name="public-vcard-contact-alias"),

    path("@<slug:slug>/qr.<str:fmt>", public_qr_download, name="public-vcard-qr"),

    path("@<slug:slug>/l/<uuid:link_id>/", track_link_click, name="public-link-click"),

    path("api/public/cards/<slug:slug>/", PublicVCardDetailView.as_view(), name="public-vcard-api"),
    path("api/public/cards/<slug:slug>/analytics/", PublicVCardAnalyticsView.as_view(), name="public-vcard-api-analytics"),
]
