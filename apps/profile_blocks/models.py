from django.db import models

from apps.core.models import BaseModel, OrderedVisibleModel
from apps.core.validators import validate_image_file


class ProfileBlockType(models.TextChoices):
    SOCIAL = "social", "Social"
    LINK = "link", "Link"
    SERVICE = "service", "Service"
    PRODUCT = "product", "Product"
    TESTIMONIAL = "testimonial", "Testimonial"
    GALLERY = "gallery", "Gallery"
    VIDEO = "video", "Video"
    CONTACT = "contact", "Contact"
    LOCATION = "location", "Location"
    APPOINTMENT = "appointment", "Appointment"
    CUSTOM = "custom", "Custom"


class ProfileBlock(BaseModel, OrderedVisibleModel):
    """
    Freeform content block (§11). `content` carries whatever shape `type`
    needs, so new block types ship without a schema migration — the
    dedicated models below (ProfileLink, Service, ...) exist for content
    that benefits from real query/filter/validation support beyond what a
    JSON blob gives you (pricing, booking flags, ratings, etc.).
    """

    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="blocks")
    type = models.CharField(max_length=20, choices=ProfileBlockType.choices)
    title = models.CharField(max_length=255, blank=True)
    content = models.JSONField(default=dict, blank=True)

    class Meta(OrderedVisibleModel.Meta):
        indexes = [models.Index(fields=["vcard", "position"])]

    def __str__(self):
        return f"{self.type} block on {self.vcard_id}"


class ProfileLink(BaseModel, OrderedVisibleModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="links")
    title = models.CharField(max_length=255)
    url = models.URLField()
    icon = models.CharField(max_length=100, blank=True)

    class Meta(OrderedVisibleModel.Meta):
        indexes = [models.Index(fields=["vcard", "position"])]

    def __str__(self):
        return f"{self.title} -> {self.url}"


class Service(BaseModel, OrderedVisibleModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    image = models.ImageField(upload_to="vcards/services/", blank=True, null=True, validators=[validate_image_file])
    booking_enabled = models.BooleanField(default=False)

    class Meta(OrderedVisibleModel.Meta):
        indexes = [models.Index(fields=["vcard", "position"])]

    def __str__(self):
        return self.name


class Product(BaseModel, OrderedVisibleModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    image = models.ImageField(upload_to="vcards/products/", blank=True, null=True, validators=[validate_image_file])
    external_url = models.URLField(blank=True)

    class Meta(OrderedVisibleModel.Meta):
        indexes = [models.Index(fields=["vcard", "position"])]

    def __str__(self):
        return self.name


class Testimonial(BaseModel, OrderedVisibleModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="testimonials")
    customer_name = models.CharField(max_length=255)
    customer_title = models.CharField(max_length=255, blank=True)
    customer_photo = models.ImageField(upload_to="vcards/testimonials/", blank=True, null=True, validators=[validate_image_file])
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta(OrderedVisibleModel.Meta):
        indexes = [models.Index(fields=["vcard", "position"])]

    def __str__(self):
        return f"{self.customer_name}: {self.content[:30]}"


class GalleryItem(BaseModel, OrderedVisibleModel):
    vcard = models.ForeignKey("cards.VCard", on_delete=models.CASCADE, related_name="gallery_items")
    image = models.ImageField(upload_to="vcards/gallery/", validators=[validate_image_file])
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    class Meta(OrderedVisibleModel.Meta):
        indexes = [models.Index(fields=["vcard", "position"])]

    def __str__(self):
        return self.title or f"Gallery item {self.id}"
