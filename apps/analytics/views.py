from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import (
    get_countries,
    get_devices,
    get_summary,
    get_time_series,
    get_top_links,
    get_traffic_sources,
    resolve_period,
)
from apps.billing.services import EntitlementService
from apps.cards.models import VCard
from apps.cards.services import accessible_vcard_ids


class VCardAnalyticsView(APIView):
    """GET /api/v1/analytics/?vcard=<id>&period=7d|30d|90d|12m|today|custom&start&end"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("vcard", OpenApiTypes.UUID, description="VCard id (required)"),
            OpenApiParameter("period", OpenApiTypes.STR, description="today|7d|30d|90d|12m|custom"),
            OpenApiParameter("start", OpenApiTypes.DATE, description="Required when period=custom"),
            OpenApiParameter("end", OpenApiTypes.DATE, description="Required when period=custom"),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        vcard_id = request.query_params.get("vcard")
        if not vcard_id:
            return Response({"detail": "vcard query param is required."}, status=status.HTTP_400_BAD_REQUEST)

        vcard = get_object_or_404(VCard, id=vcard_id, id__in=accessible_vcard_ids(request.user))

        tenant = vcard.organization or vcard.owner
        if not EntitlementService(tenant).can("analytics"):
            return Response({"detail": "Analytics is not available on the current plan."}, status=status.HTTP_402_PAYMENT_REQUIRED)

        period = request.query_params.get("period", "7d")
        start_date, end_date = resolve_period(
            period, request.query_params.get("start"), request.query_params.get("end")
        )

        return Response({
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "summary": get_summary(vcard, start_date, end_date),
            "time_series": get_time_series(vcard, start_date, end_date),
            "top_links": get_top_links(vcard, start_date, end_date),
            "traffic_sources": get_traffic_sources(vcard, start_date, end_date),
            "countries": get_countries(vcard, start_date, end_date),
            "devices": get_devices(vcard, start_date, end_date),
        })
