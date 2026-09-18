from django.contrib import admin

from apps.profile_blocks.models import GalleryItem, Product, ProfileBlock, ProfileLink, Service, Testimonial


@admin.register(ProfileBlock)
class ProfileBlockAdmin(admin.ModelAdmin):
    list_display = ["vcard", "type", "title", "position", "is_visible"]
    list_filter = ["type", "is_visible"]


@admin.register(ProfileLink)
class ProfileLinkAdmin(admin.ModelAdmin):
    list_display = ["vcard", "title", "url", "position", "is_visible"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["vcard", "name", "price", "currency", "booking_enabled", "is_visible"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["vcard", "name", "price", "currency", "is_visible"]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["vcard", "customer_name", "rating", "is_visible"]


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ["vcard", "title", "position", "is_visible"]
