from django.core.cache import cache
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.cards.models import VCard
from apps.cards.serializers import PublicVCardAnalyticsSerializer, VCardPublicSerializer
from apps.nfc_qr.qr import generate_qr_for_vcard
from apps.nfc_qr.vcard import build_vcf

PUBLIC_CACHE_TTL = 300  # 5 minutes; busted immediately on update via signals


def _get_public_vcard_or_404(slug: str) -> VCard:
    vcard = get_object_or_404(
        VCard.objects.select_related("template").prefetch_related(
            "links", "services", "products", "testimonials", "gallery_items", "blocks",
        ),
        slug=slug,
    )
    if not vcard.is_publicly_viewable:
        raise Http404("This card is not currently public.")
    return vcard


@require_GET
def render_public_card(request, slug):
    """Server-rendered public card page (§22): SEO/OG/JSON-LD, and the core
    profile content must be present before any JS runs — this is a plain
    Django template render, not an SPA shell."""
    cache_key = f"public_card_html:{slug}"
    cached = cache.get(cache_key)
    if cached is not None:
        return HttpResponse(cached)

    vcard = _get_public_vcard_or_404(slug)

    from apps.analytics.tasks import record_card_view
    from apps.core.utils import get_client_ip

    record_card_view.delay(
        str(vcard.id), get_client_ip(request), request.META.get("HTTP_REFERER", ""),
        request.META.get("HTTP_USER_AGENT", ""),
    )

    context = {
        "vcard": vcard,
        "links": vcard.links.filter(is_visible=True),
        "services": vcard.services.filter(is_visible=True),
        "products": vcard.products.filter(is_visible=True),
        "testimonials": vcard.testimonials.filter(is_visible=True),
        "gallery_items": vcard.gallery_items.filter(is_visible=True),
        "blocks": vcard.blocks.filter(is_visible=True).order_by("position"),
    }
    response = render(request, "cards/public_card.html", context)
    cache.set(cache_key, response.content, PUBLIC_CACHE_TTL)
    return response


class PublicVCardDetailView(RetrieveAPIView):
    """JSON counterpart of the same public data (§39) for API/mobile
    consumers — never exposes private analytics/billing/internal org info."""

    serializer_class = VCardPublicSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_field = "slug"
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public-card"

    def get_object(self):
        return _get_public_vcard_or_404(self.kwargs["slug"])


class PublicVCardAnalyticsView(APIView):
    """Only a small, non-identifying aggregate — never referrer/device/
    country breakdowns or raw events (§25, §39)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public-card"

    @extend_schema(responses=PublicVCardAnalyticsSerializer)
    def get(self, request, slug):
        vcard = _get_public_vcard_or_404(slug)
        from apps.analytics.models import CardView

        total_views = CardView.objects.filter(vcard=vcard).count()
        return Response({"total_views": total_views})


@require_GET
def public_vcf_download(request, slug):
    vcard = _get_public_vcard_or_404(slug)

    from apps.analytics.tasks import record_contact_download
    from apps.core.utils import get_client_ip

    record_contact_download.delay(str(vcard.id), get_client_ip(request))

    vcf_bytes = build_vcf(vcard)
    response = HttpResponse(vcf_bytes, content_type="text/vcard")
    response["Content-Disposition"] = f'attachment; filename="{vcard.slug}.vcf"'
    return response


@require_GET
def track_link_click(request, slug, link_id):
    """Redirect-through tracker so a plain <a href> click can be logged
    server-side with no JavaScript (mirrors the no-JS .vcf download)."""
    vcard = _get_public_vcard_or_404(slug)
    link = get_object_or_404(vcard.links, id=link_id, is_visible=True)

    from apps.analytics.tasks import record_link_click
    from apps.core.utils import get_client_ip

    record_link_click.delay(
        str(vcard.id), str(link.id), get_client_ip(request),
        request.META.get("HTTP_REFERER", ""), request.META.get("HTTP_USER_AGENT", ""),
    )
    return HttpResponseRedirect(link.url)


@require_GET
def public_qr_download(request, slug, fmt):
    vcard = _get_public_vcard_or_404(slug)
    try:
        content, content_type = generate_qr_for_vcard(vcard, fmt)
    except ValueError:
        raise Http404("Unsupported QR format.")
    return HttpResponse(content, content_type=content_type)
