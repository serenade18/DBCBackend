from django.db import models

from apps.core.models import BaseModel


class NfcMaterial(models.TextChoices):
    PET_PLASTIC = "pet_plastic", "PET Plastic"
    WOOD = "wood", "Wood"
    METAL = "metal", "Metal"


class NfcCardStatus(models.TextChoices):
    INVENTORY = "inventory", "Inventory"
    RESERVED = "reserved", "Reserved"
    ASSIGNED = "assigned", "Assigned"
    ACTIVE = "active", "Active"
    BLOCKED = "blocked", "Blocked"
    RETIRED = "retired", "Retired"


class NfcCard(BaseModel):
    """
    Physical NFC tag inventory (§21, §33). The chip is written with the
    VCard's public URL only — never profile data — so re-pointing a card to
    a different profile never requires rewriting the physical chip.
    """

    uid = models.CharField(max_length=64, unique=True, help_text="Chip UID reported by the NFC hardware.")
    serial_number = models.CharField(max_length=64, unique=True, blank=True)
    material = models.CharField(max_length=20, choices=NfcMaterial.choices, default=NfcMaterial.PET_PLASTIC)
    vcard = models.ForeignKey("cards.VCard", on_delete=models.SET_NULL, related_name="nfc_cards", null=True, blank=True)
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, related_name="nfc_cards", null=True, blank=True)
    status = models.CharField(max_length=20, choices=NfcCardStatus.choices, default=NfcCardStatus.INVENTORY)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"NFC {self.serial_number or self.uid} ({self.status})"

    @property
    def write_payload(self) -> str:
        """The single value that should be written to the NFC chip."""
        return self.vcard.public_url if self.vcard else ""
