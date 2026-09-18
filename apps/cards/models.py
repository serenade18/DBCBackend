from django.db import models

from apps.core.models import BaseModel

DEFAULT_THEME_CONFIG = {
    "primaryColor": "#111827",
    "secondaryColor": "#6B7280",
    "backgroundColor": "#FFFFFF",
    "textColor": "#111827",
    "buttonStyle": "rounded",
    "cardStyle": "glass",
    "fontFamily": "Inter",
    "borderRadius": "lg",
}


class VCardStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class VCardVisibility(models.TextChoices):
    PUBLIC = "public", "Public"
    UNLISTED = "unlisted", "Unlisted"
    PRIVATE = "private", "Private"


class VCard(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="vcards", null=True, blank=True
    )
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="owned_vcards")
    assigned_user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="assigned_vcards", null=True, blank=True
    )

    slug = models.SlugField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)

    profile_photo = models.ImageField(upload_to="vcards/profile/", blank=True, null=True)
    cover_photo = models.ImageField(upload_to="vcards/cover/", blank=True, null=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)

    template = models.ForeignKey(
        "templates.CardTemplate", on_delete=models.SET_NULL, related_name="vcards", null=True, blank=True
    )
    theme_config = models.JSONField(default=dict, blank=True)

    visibility = models.CharField(max_length=20, choices=VCardVisibility.choices, default=VCardVisibility.PUBLIC)
    status = models.CharField(max_length=20, choices=VCardStatus.choices, default=VCardStatus.DRAFT)
    is_featured = models.BooleanField(default=False)
    is_directory_visible = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.display_name} (@{self.slug})"

    def save(self, *args, **kwargs):
        if not self.theme_config:
            self.theme_config = dict(DEFAULT_THEME_CONFIG)
        super().save(*args, **kwargs)

    @property
    def public_url(self) -> str:
        from django.conf import settings

        return f"{settings.PUBLIC_BASE_URL}/@{self.slug}"

    @property
    def is_publicly_viewable(self) -> bool:
        return self.status == VCardStatus.PUBLISHED and self.visibility != VCardVisibility.PRIVATE
