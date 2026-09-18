from django.urls import path

from apps.profile_blocks.views import (
    GalleryItemDetailView,
    GalleryItemListCreateView,
    ProductDetailView,
    ProductListCreateView,
    ProfileBlockDetailView,
    ProfileBlockListCreateView,
    ProfileBlockReorderView,
    ProfileLinkDetailView,
    ProfileLinkListCreateView,
    ServiceDetailView,
    ServiceListCreateView,
    TestimonialDetailView,
    TestimonialListCreateView,
)

urlpatterns = [
    # Blocks
    path("vcards/<uuid:vcard_id>/blocks/", ProfileBlockListCreateView.as_view(), name="block-list"),
    path("vcards/<uuid:vcard_id>/blocks/reorder/", ProfileBlockReorderView.as_view(), name="block-reorder"),
    path("blocks/<uuid:pk>/", ProfileBlockDetailView.as_view(), name="block-detail"),

    # Links
    path("vcards/<uuid:vcard_id>/links/", ProfileLinkListCreateView.as_view(), name="link-list"),
    path("links/<uuid:pk>/", ProfileLinkDetailView.as_view(), name="link-detail"),

    # Services
    path("vcards/<uuid:vcard_id>/services/", ServiceListCreateView.as_view(), name="service-list"),
    path("services/<uuid:pk>/", ServiceDetailView.as_view(), name="service-detail"),

    # Products
    path("vcards/<uuid:vcard_id>/products/", ProductListCreateView.as_view(), name="product-list"),
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="product-detail"),

    # Testimonials
    path("vcards/<uuid:vcard_id>/testimonials/", TestimonialListCreateView.as_view(), name="testimonial-list"),
    path("testimonials/<uuid:pk>/", TestimonialDetailView.as_view(), name="testimonial-detail"),

    # Gallery
    path("vcards/<uuid:vcard_id>/gallery-items/", GalleryItemListCreateView.as_view(), name="gallery-item-list"),
    path("gallery-items/<uuid:pk>/", GalleryItemDetailView.as_view(), name="gallery-item-detail"),
]
