from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.cards.models import VCard, VCardStatus


def generate_unique_slug(base_text: str, instance: VCard | None = None) -> str:
    base_slug = slugify(base_text) or "card"
    slug = base_slug
    suffix = 1
    qs = VCard.objects.all()
    if instance is not None:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(slug=slug).exists():
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    return slug


REQUIRED_FOR_PUBLISH = ["display_name"]


def publish_vcard(vcard: VCard) -> list[str]:
    """Returns a list of validation errors; publishes and returns [] on
    success. Kept as plain validation (not a form/serializer) since it's
    also invoked from the assign/reassign flow indirectly via services."""
    errors = [field for field in REQUIRED_FOR_PUBLISH if not getattr(vcard, field)]
    if errors:
        return [f"'{field}' is required to publish a card." for field in errors]

    vcard.status = VCardStatus.PUBLISHED
    if not vcard.published_at:
        vcard.published_at = timezone.now()
    vcard.save(update_fields=["status", "published_at"])
    return []


def unpublish_vcard(vcard: VCard):
    vcard.status = VCardStatus.DRAFT
    vcard.save(update_fields=["status"])


def assign_vcard(vcard: VCard, user) -> None:
    vcard.assigned_user = user
    vcard.save(update_fields=["assigned_user"])


def unassign_vcard(vcard: VCard) -> None:
    vcard.assigned_user = None
    vcard.save(update_fields=["assigned_user"])


def can_manage_vcard(user, vcard: VCard) -> bool:
    """Shared by profile_blocks/appointments/enquiries: who may edit a
    card's content, not just view it."""
    if not user or not user.is_authenticated:
        return False
    if vcard.owner_id == user.id or vcard.assigned_user_id == user.id:
        return True
    if vcard.organization_id:
        from apps.core.permissions import get_member_role

        return get_member_role(user, vcard.organization) in {"owner", "admin"}
    return False


def accessible_vcard_ids(user):
    """VCard ids the user may view/manage: owned, assigned, or within an
    organization they're an active member of."""
    from apps.core.permissions import get_active_memberships

    org_ids = [m.organization_id for m in get_active_memberships(user)]
    return VCard.objects.filter(
        models.Q(owner=user) | models.Q(assigned_user=user) | models.Q(organization_id__in=org_ids)
    ).values_list("id", flat=True)
