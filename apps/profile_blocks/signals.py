from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.cards.signals import bust_public_card_cache
from apps.profile_blocks.models import GalleryItem, Product, ProfileBlock, ProfileLink, Service, Testimonial

CONTENT_MODELS = [ProfileBlock, ProfileLink, Service, Product, Testimonial, GalleryItem]


def _bust(sender, instance, **kwargs):
    bust_public_card_cache(instance.vcard.slug)


for model in CONTENT_MODELS:
    post_save.connect(_bust, sender=model, weak=False)
    post_delete.connect(_bust, sender=model, weak=False)
