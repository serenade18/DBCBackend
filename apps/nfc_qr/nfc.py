from django.utils import timezone

from apps.nfc_qr.models import NfcCard, NfcCardStatus


class NfcTransitionError(Exception):
    pass


def assign_card(nfc_card: NfcCard, vcard) -> NfcCard:
    """Unassigned -> Assigned (§21)."""
    if nfc_card.status not in {NfcCardStatus.INVENTORY, NfcCardStatus.RESERVED}:
        raise NfcTransitionError(f"Cannot assign a card in status '{nfc_card.status}'.")
    nfc_card.vcard = vcard
    nfc_card.status = NfcCardStatus.ASSIGNED
    nfc_card.save(update_fields=["vcard", "status"])
    return nfc_card


def activate_card(nfc_card: NfcCard) -> NfcCard:
    """Assigned -> Activated."""
    if nfc_card.status != NfcCardStatus.ASSIGNED:
        raise NfcTransitionError("Only an assigned card can be activated.")
    nfc_card.status = NfcCardStatus.ACTIVE
    nfc_card.activated_at = timezone.now()
    nfc_card.save(update_fields=["status", "activated_at"])
    return nfc_card


def suspend_card(nfc_card: NfcCard) -> NfcCard:
    """Activated -> Suspended."""
    if nfc_card.status not in {NfcCardStatus.ACTIVE, NfcCardStatus.ASSIGNED}:
        raise NfcTransitionError("Only an assigned/active card can be suspended.")
    nfc_card.status = NfcCardStatus.BLOCKED
    nfc_card.save(update_fields=["status"])
    return nfc_card


def reassign_card(nfc_card: NfcCard, new_vcard) -> NfcCard:
    """Suspended/Active/Assigned -> Reassigned to a different profile. The
    physical chip doesn't need rewriting — only the URL it points to (the
    VCard's slug) can change server-side, but reassigning to a *different*
    VCard record does require the chip to be rewritten with that VCard's URL."""
    if nfc_card.status not in {NfcCardStatus.ACTIVE, NfcCardStatus.ASSIGNED, NfcCardStatus.BLOCKED}:
        raise NfcTransitionError(f"Cannot reassign a card in status '{nfc_card.status}'.")
    nfc_card.vcard = new_vcard
    nfc_card.status = NfcCardStatus.ASSIGNED
    nfc_card.save(update_fields=["vcard", "status"])
    return nfc_card


def retire_card(nfc_card: NfcCard) -> NfcCard:
    nfc_card.status = NfcCardStatus.RETIRED
    nfc_card.vcard = None
    nfc_card.save(update_fields=["status", "vcard"])
    return nfc_card


def write_instructions(nfc_card: NfcCard) -> dict:
    """Payload/instructions for whatever writes the physical chip (an admin
    tool, a mobile app with NFC write capability, ...)."""
    return {
        "uid": nfc_card.uid,
        "record_type": "URI",
        "payload": nfc_card.write_payload,
        "lock_after_write": True,
    }
