from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.cards.models import VCard


def bust_public_card_cache(slug: str):
    cache.delete(f"public_card_html:{slug}")


@receiver(post_save, sender=VCard)
def on_vcard_saved(sender, instance, **kwargs):
    bust_public_card_cache(instance.slug)


@receiver(post_delete, sender=VCard)
def on_vcard_deleted(sender, instance, **kwargs):
    bust_public_card_cache(instance.slug)
