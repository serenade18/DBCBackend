import logging

from celery import shared_task
from django.utils import timezone
from user_agents import parse as parse_user_agent

from apps.core.utils import hash_ip

logger = logging.getLogger("django")


def _device_and_browser(user_agent_string: str) -> tuple[str, str]:
    if not user_agent_string:
        return "", ""
    ua = parse_user_agent(user_agent_string)
    if ua.is_mobile:
        device = "mobile"
    elif ua.is_tablet:
        device = "tablet"
    elif ua.is_pc:
        device = "desktop"
    else:
        device = "other"
    return device, ua.browser.family or ""


def _classify_source(referrer: str) -> str:
    if not referrer:
        return "direct"
    referrer_lower = referrer.lower()
    for needle, source in (
        ("google.", "google"), ("facebook.", "facebook"), ("instagram.", "instagram"),
        ("linkedin.", "linkedin"), ("twitter.", "twitter"), ("x.com", "twitter"),
        ("t.co", "twitter"),
    ):
        if needle in referrer_lower:
            return source
    return "referral"


@shared_task
def record_card_view(vcard_id, ip_address, referrer, user_agent_string):
    from apps.analytics.models import CardView

    device_type, browser = _device_and_browser(user_agent_string)
    CardView.objects.create(
        vcard_id=vcard_id,
        referrer=referrer[:500],
        source=_classify_source(referrer),
        device_type=device_type,
        browser=browser,
        ip_hash=hash_ip(ip_address),
        user_agent_hash=hash_ip(user_agent_string),
    )


@shared_task
def record_link_click(vcard_id, link_id, ip_address, referrer, user_agent_string):
    from apps.analytics.models import LinkClick

    device_type, _ = _device_and_browser(user_agent_string)
    LinkClick.objects.create(
        vcard_id=vcard_id,
        link_id=link_id,
        source=_classify_source(referrer),
        device_type=device_type,
        ip_hash=hash_ip(ip_address),
    )


@shared_task
def record_contact_download(vcard_id, ip_address):
    from apps.analytics.models import ContactDownload

    ContactDownload.objects.create(vcard_id=vcard_id, ip_hash=hash_ip(ip_address))


@shared_task
def aggregate_analytics():
    """Hourly rollup (§26, §48): folds today's raw events into
    DailyCardStat so dashboard reads don't scan raw event tables."""
    from apps.analytics.models import CardView, ContactDownload, DailyCardStat, LinkClick
    from apps.appointments.models import Appointment
    from apps.enquiries.models import Enquiry

    today = timezone.localdate()
    day_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    day_end = day_start + timezone.timedelta(days=1)

    vcard_ids = set(
        CardView.objects.filter(timestamp__gte=day_start, timestamp__lt=day_end).values_list("vcard_id", flat=True)
    )
    for vcard_id in vcard_ids:
        views_qs = CardView.objects.filter(vcard_id=vcard_id, timestamp__gte=day_start, timestamp__lt=day_end)
        DailyCardStat.objects.update_or_create(
            vcard_id=vcard_id, date=today,
            defaults={
                "views": views_qs.count(),
                "unique_visitors": views_qs.values("ip_hash").distinct().count(),
                "link_clicks": LinkClick.objects.filter(
                    vcard_id=vcard_id, timestamp__gte=day_start, timestamp__lt=day_end
                ).count(),
                "contact_downloads": ContactDownload.objects.filter(
                    vcard_id=vcard_id, timestamp__gte=day_start, timestamp__lt=day_end
                ).count(),
                "enquiries": Enquiry.objects.filter(
                    vcard_id=vcard_id, created_at__gte=day_start, created_at__lt=day_end
                ).count(),
                "appointments": Appointment.objects.filter(
                    vcard_id=vcard_id, created_at__gte=day_start, created_at__lt=day_end
                ).count(),
            },
        )
    logger.info("Aggregated analytics for %d vcards on %s", len(vcard_ids), today)
