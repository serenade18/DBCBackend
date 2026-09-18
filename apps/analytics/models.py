from django.db import models

from apps.core.models import BaseModel


class CardView(BaseModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="views")
    timestamp = models.DateTimeField(auto_now_add=True)
    referrer = models.CharField(max_length=500, blank=True)
    source = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    # Raw IPs/user agents are never stored — only one-way hashes (§25, §41),
    # kept purely for coarse dedup/abuse signal, never exposed to org users.
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["vcard", "timestamp"]),
        ]


class LinkClick(BaseModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="link_clicks")
    link = models.ForeignKey("profile_blocks.ProfileLink", on_delete=models.SET_NULL, null=True, blank=True, related_name="clicks")
    timestamp = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["vcard", "timestamp"]),
        ]


class ContactDownload(BaseModel):
    """.vcf download event — tracked separately from CardView so a page
    view and a 'save contact' action aren't conflated in the metrics §26
    asks for ('Total Views' vs. 'Contact Downloads')."""

    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="contact_downloads")
    timestamp = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["vcard", "timestamp"])]


class DailyCardStat(BaseModel):
    """
    Hourly-aggregated rollup (§26) the dashboard reads for time-series and
    totals, instead of scanning raw CardView/LinkClick rows per request.
    Top-links/traffic-source/country/device *breakdowns* still query the
    raw tables directly for a given range — acceptable at this scale; move
    those to their own rollup tables if/when raw-event volume makes that
    slow.
    """

    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="daily_stats")
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    link_clicks = models.PositiveIntegerField(default=0)
    contact_downloads = models.PositiveIntegerField(default=0)
    enquiries = models.PositiveIntegerField(default=0)
    appointments = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        constraints = [models.UniqueConstraint(fields=["vcard", "date"], name="unique_vcard_daily_stat")]
        indexes = [models.Index(fields=["vcard", "date"])]
