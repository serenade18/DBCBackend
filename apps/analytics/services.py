from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.analytics.models import CardView, DailyCardStat, LinkClick

PERIOD_DAYS = {
    "today": 0,
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "12m": 365,
}


def resolve_period(period: str, start=None, end=None) -> tuple:
    today = timezone.localdate()
    if period == "custom" and start and end:
        from datetime import date as date_cls

        return date_cls.fromisoformat(start), date_cls.fromisoformat(end)
    days = PERIOD_DAYS.get(period, 7)
    return today - timedelta(days=days), today


def get_summary(vcard, start_date, end_date) -> dict:
    stats = DailyCardStat.objects.filter(vcard=vcard, date__gte=start_date, date__lte=end_date)
    totals = stats.aggregate(
        total_views=_sum("views"), unique_visitors=_sum("unique_visitors"),
        link_clicks=_sum("link_clicks"), contact_downloads=_sum("contact_downloads"),
        enquiries=_sum("enquiries"), appointments=_sum("appointments"),
    )
    return {k: v or 0 for k, v in totals.items()}


def _sum(field):
    from django.db.models import Sum

    return Sum(field)


def get_time_series(vcard, start_date, end_date) -> list:
    stats = DailyCardStat.objects.filter(vcard=vcard, date__gte=start_date, date__lte=end_date).order_by("date")
    return [
        {
            "date": s.date.isoformat(), "views": s.views, "link_clicks": s.link_clicks,
            "engagement_rate": round((s.link_clicks / s.views) * 100, 2) if s.views else 0,
        }
        for s in stats
    ]


def get_top_links(vcard, start_date, end_date, limit=10) -> list:
    end_dt = timezone.make_aware(timezone.datetime.combine(end_date + timedelta(days=1), timezone.datetime.min.time()))
    start_dt = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
    rows = (
        LinkClick.objects.filter(vcard=vcard, timestamp__gte=start_dt, timestamp__lt=end_dt, link__isnull=False)
        .values("link_id", "link__title")
        .annotate(clicks=Count("id"))
        .order_by("-clicks")[:limit]
    )
    return [{"link_id": str(r["link_id"]), "title": r["link__title"], "clicks": r["clicks"]} for r in rows]


def _breakdown(queryset, field, start_dt, end_dt, vcard, limit=10):
    rows = (
        queryset.filter(vcard=vcard, timestamp__gte=start_dt, timestamp__lt=end_dt)
        .exclude(**{f"{field}__exact": ""})
        .values(field)
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )
    return [{field: r[field], "count": r["count"]} for r in rows]


def get_traffic_sources(vcard, start_date, end_date) -> list:
    start_dt, end_dt = _date_range(start_date, end_date)
    return _breakdown(CardView.objects, "source", start_dt, end_dt, vcard)


def get_countries(vcard, start_date, end_date) -> list:
    start_dt, end_dt = _date_range(start_date, end_date)
    return _breakdown(CardView.objects, "country", start_dt, end_dt, vcard)


def get_devices(vcard, start_date, end_date) -> list:
    start_dt, end_dt = _date_range(start_date, end_date)
    return _breakdown(CardView.objects, "device_type", start_dt, end_dt, vcard)


def _date_range(start_date, end_date):
    start_dt = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
    end_dt = timezone.make_aware(timezone.datetime.combine(end_date + timedelta(days=1), timezone.datetime.min.time()))
    return start_dt, end_dt
