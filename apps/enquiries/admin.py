from django.contrib import admin

from apps.enquiries.models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "vcard", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "email", "vcard__slug"]
