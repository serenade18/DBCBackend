from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services import EntitlementService
from apps.cards.models import VCard
from apps.cards.services import can_manage_vcard
from apps.core.exceptions import EntitlementError
from apps.profile_blocks.models import GalleryItem, Product, ProfileBlock, ProfileLink, Service, Testimonial
from apps.profile_blocks.serializers import (
    GalleryItemSerializer,
    ProductSerializer,
    ProfileBlockSerializer,
    ProfileLinkSerializer,
    ReorderSerializer,
    ServiceSerializer,
    TestimonialSerializer,
)


def _get_manageable_vcard(user, vcard_id):
    vcard = get_object_or_404(VCard, id=vcard_id)
    if not can_manage_vcard(user, vcard):
        return None
    return vcard


class VCardScopedListCreateView(generics.ListCreateAPIView):
    """Base for the six content types hung off a VCard (blocks, links,
    services, products, testimonials, gallery items): list/create scoped to
    a parent VCard the requesting user may manage."""

    model = None
    related_name = None
    permission_classes = [IsAuthenticated]
    entitlement_check = None  # optional: (EntitlementService, count) -> bool

    def get_vcard(self):
        vcard = _get_manageable_vcard(self.request.user, self.kwargs["vcard_id"])
        if vcard is None:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to manage this card.")
        return vcard

    def get_queryset(self):
        vcard = self.get_vcard()
        return getattr(vcard, self.related_name).all()

    def perform_create(self, serializer):
        vcard = self.get_vcard()
        if self.entitlement_check:
            current_count = getattr(vcard, self.related_name).count()
            tenant = vcard.organization or vcard.owner
            if not self.entitlement_check(EntitlementService(tenant), current_count):
                raise EntitlementError(f"Plan limit reached for {self.related_name}.")
        serializer.save(vcard=vcard)


class VCardScopedDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Base for the flat /api/v1/<things>/{id}/ endpoints."""

    model = None
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self):
        obj = super().get_object()
        if not can_manage_vcard(self.request.user, obj.vcard):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to manage this card.")
        return obj


# --- Blocks -------------------------------------------------------------

class ProfileBlockListCreateView(VCardScopedListCreateView):
    model = ProfileBlock
    related_name = "blocks"
    serializer_class = ProfileBlockSerializer


class ProfileBlockDetailView(VCardScopedDetailView):
    model = ProfileBlock
    serializer_class = ProfileBlockSerializer


class ProfileBlockReorderView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ReorderSerializer, responses={200: ProfileBlockSerializer(many=True)})
    def post(self, request, vcard_id):
        vcard = _get_manageable_vcard(request.user, vcard_id)
        if vcard is None:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["order"]

        blocks = {str(b.id): b for b in vcard.blocks.filter(id__in=ids)}
        updated = []
        for position, block_id in enumerate(ids):
            block = blocks.get(str(block_id))
            if block:
                block.position = position
                updated.append(block)
        ProfileBlock.objects.bulk_update(updated, ["position"])
        return Response(ProfileBlockSerializer(vcard.blocks.all(), many=True).data)


# --- Links ----------------------------------------------------------------

class ProfileLinkListCreateView(VCardScopedListCreateView):
    model = ProfileLink
    related_name = "links"
    serializer_class = ProfileLinkSerializer


class ProfileLinkDetailView(VCardScopedDetailView):
    model = ProfileLink
    serializer_class = ProfileLinkSerializer


# --- Services ---------------------------------------------------------------

class ServiceListCreateView(VCardScopedListCreateView):
    model = Service
    related_name = "services"
    serializer_class = ServiceSerializer
    entitlement_check = staticmethod(lambda es, count: es.can_add_service(count))


class ServiceDetailView(VCardScopedDetailView):
    model = Service
    serializer_class = ServiceSerializer


# --- Products -----------------------------------------------------------

class ProductListCreateView(VCardScopedListCreateView):
    model = Product
    related_name = "products"
    serializer_class = ProductSerializer
    entitlement_check = staticmethod(lambda es, count: es.can_add_product(count))


class ProductDetailView(VCardScopedDetailView):
    model = Product
    serializer_class = ProductSerializer


# --- Testimonials -----------------------------------------------------------

class TestimonialListCreateView(VCardScopedListCreateView):
    model = Testimonial
    related_name = "testimonials"
    serializer_class = TestimonialSerializer


class TestimonialDetailView(VCardScopedDetailView):
    model = Testimonial
    serializer_class = TestimonialSerializer


# --- Gallery ------------------------------------------------------------

class GalleryItemListCreateView(VCardScopedListCreateView):
    model = GalleryItem
    related_name = "gallery_items"
    serializer_class = GalleryItemSerializer
    entitlement_check = staticmethod(lambda es, count: es.can_add_gallery_item(count))


class GalleryItemDetailView(VCardScopedDetailView):
    model = GalleryItem
    serializer_class = GalleryItemSerializer
