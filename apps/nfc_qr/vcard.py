import vobject


def build_vcf(vcard) -> bytes:
    """Builds a standards-compliant .vcf (vCard 3.0) file for a VCard (§19).
    Must work without JavaScript — this is a plain file download."""
    card = vobject.vCard()

    card.add("n")
    name_parts = (vcard.display_name or "").split(" ", 1)
    given = name_parts[0] if name_parts else ""
    family = name_parts[1] if len(name_parts) > 1 else ""
    card.n.value = vobject.vcard.Name(family=family, given=given)

    card.add("fn")
    card.fn.value = vcard.display_name

    if vcard.company_name:
        card.add("org")
        card.org.value = [vcard.company_name]

    if vcard.job_title:
        card.add("title")
        card.title.value = vcard.job_title

    if vcard.phone:
        tel = card.add("tel")
        tel.value = vcard.phone
        tel.type_param = "CELL"

    if vcard.whatsapp and vcard.whatsapp != vcard.phone:
        tel = card.add("tel")
        tel.value = vcard.whatsapp
        tel.type_param = "WHATSAPP"

    if vcard.email:
        email = card.add("email")
        email.value = vcard.email
        email.type_param = "INTERNET"

    if vcard.website:
        card.add("url")
        card.url.value = vcard.website

    if vcard.address:
        adr = card.add("adr")
        adr.value = vobject.vcard.Address(street=vcard.address)
        adr.type_param = "WORK"

    if vcard.profile_photo:
        try:
            vcard.profile_photo.open("rb")
            photo_bytes = vcard.profile_photo.read()
            photo = card.add("photo")
            photo.value = photo_bytes
            photo.encoding_param = "b"
            photo.type_param = "JPEG"
        except (ValueError, OSError):
            pass  # file missing from storage — skip embedding, rest of vCard still valid

    card.add("url")
    card.url_list[-1].value = vcard.public_url

    for link in vcard.links.filter(is_visible=True).order_by("position"):
        url_field = card.add("url")
        url_field.value = link.url

    return card.serialize().encode("utf-8")
