from django.contrib import admin

from apps.analytics.models import CardView, ContactDownload, DailyCardStat, LinkClick


@admin.register(CardView)
class CardViewAdmin(admin.ModelAdmin):
    list_display = ["vcard", "timestamp", "source", "device_type", "country"]
    list_filter = ["source", "device_type", "country"]
    date_hierarchy = "timestamp"


@admin.register(LinkClick)
class LinkClickAdmin(admin.ModelAdmin):
    list_display = ["vcard", "link", "timestamp", "source", "device_type"]
    date_hierarchy = "timestamp"


@admin.register(ContactDownload)
class ContactDownloadAdmin(admin.ModelAdmin):
    list_display = ["vcard", "timestamp"]
    date_hierarchy = "timestamp"


@admin.register(DailyCardStat)
class DailyCardStatAdmin(admin.ModelAdmin):
    list_display = ["vcard", "date", "views", "unique_visitors", "link_clicks"]
    date_hierarchy = "date"
