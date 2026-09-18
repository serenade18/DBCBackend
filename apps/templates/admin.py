from django.contrib import admin

from apps.templates.models import CardTemplate


@admin.register(CardTemplate)
class CardTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "is_active", "is_premium"]
    list_filter = ["category", "is_active", "is_premium"]
    prepopulated_fields = {"slug": ("name",)}
