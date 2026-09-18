from django.contrib import admin

from apps.nfc_qr.models import NfcCard


@admin.register(NfcCard)
class NfcCardAdmin(admin.ModelAdmin):
    list_display = ["serial_number", "uid", "material", "status", "vcard", "activated_at"]
    list_filter = ["status", "material"]
    search_fields = ["uid", "serial_number", "vcard__slug"]
    autocomplete_fields = ["vcard", "order"]
