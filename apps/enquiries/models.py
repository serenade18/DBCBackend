from django.db import models

from apps.core.models import BaseModel


class EnquiryStatus(models.TextChoices):
    NEW = "new", "New"
    READ = "read", "Read"
    REPLIED = "replied", "Replied"
    ARCHIVED = "archived", "Archived"


class Enquiry(BaseModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="enquiries")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=EnquiryStatus.choices, default=EnquiryStatus.NEW)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["vcard", "status"])]

    def __str__(self):
        return f"{self.name} -> {self.vcard_id}"
