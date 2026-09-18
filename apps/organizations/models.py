from django.db import models

from apps.core.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.ImageField(upload_to="organizations/logos/", blank=True, null=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=2, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name


class OrganizationRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"


class MembershipStatus(models.TextChoices):
    INVITED = "invited", "Invited"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    REMOVED = "removed", "Removed"


class OrganizationMember(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="organization_memberships")
    role = models.CharField(max_length=20, choices=OrganizationRole.choices, default=OrganizationRole.MEMBER)
    status = models.CharField(max_length=20, choices=MembershipStatus.choices, default=MembershipStatus.INVITED)
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "user"], name="unique_org_member"),
        ]
        indexes = [models.Index(fields=["organization", "status"])]

    def __str__(self):
        return f"{self.user_id} @ {self.organization_id} ({self.role})"
