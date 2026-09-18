from django.contrib import admin

from apps.orders.models import Order, OrderItem, PhysicalCardProduct, ShippingAddress, ShippingEvent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class ShippingEventInline(admin.TabularInline):
    model = ShippingEvent
    extra = 0


@admin.register(PhysicalCardProduct)
class PhysicalCardProductAdmin(admin.ModelAdmin):
    list_display = ["name", "material", "price", "currency", "is_active"]
    list_filter = ["material", "is_active"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "customer", "organization", "status", "payment_status", "total", "created_at"]
    list_filter = ["status", "payment_status"]
    search_fields = ["order_number", "customer__email", "organization__name"]
    inlines = [OrderItemInline, ShippingEventInline]


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ["full_name", "city", "country", "phone"]
