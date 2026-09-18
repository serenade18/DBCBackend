import random
import string

from django.db import models

from apps.core.models import BaseModel
from apps.core.validators import validate_image_file


class PhysicalCardProduct(BaseModel):
    class Material(models.TextChoices):
        PET_PLASTIC = "pet_plastic", "PET Plastic"
        WOOD = "wood", "Wood"
        METAL = "metal", "Metal"

    name = models.CharField(max_length=255)
    material = models.CharField(max_length=20, choices=Material.choices)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    image = models.ImageField(upload_to="products/nfc-cards/", blank=True, null=True, validators=[validate_image_file])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ShippingAddress(BaseModel):
    full_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, verbose_name="County / State")
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.full_name}, {self.city}, {self.country}"


class OrderStatus(models.TextChoices):
    PENDING_PAYMENT = "pending_payment", "Pending payment"
    PAID = "paid", "Paid"
    PROCESSING = "processing", "Processing"
    PRINTING = "printing", "Printing"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


def generate_order_number() -> str:
    return "ORD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Order(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.SET_NULL, related_name="orders", null=True, blank=True
    )
    customer = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, related_name="orders", null=True)
    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING_PAYMENT)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")

    shipping_address = models.OneToOneField(ShippingAddress, on_delete=models.PROTECT, related_name="order")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.order_number


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(PhysicalCardProduct, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vcard = models.ForeignKey(
        "cards.VCard", on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items",
        help_text="Which card this physical unit should be provisioned for.",
    )

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class ShippingEvent(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="shipping_events")
    status = models.CharField(max_length=20, choices=OrderStatus.choices)
    description = models.CharField(max_length=255, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.order.order_number}: {self.status}"
