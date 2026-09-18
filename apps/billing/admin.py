from django.contrib import admin

from apps.billing.models import Payment, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "monthly_price", "annual_price", "currency", "is_active"]
    list_filter = ["is_active"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "organization", "owner", "plan", "provider", "status", "current_period_end"]
    list_filter = ["status", "provider", "plan"]
    search_fields = ["organization__name", "owner__email", "provider_subscription_id"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["__str__", "organization", "owner", "provider", "status", "paid_at"]
    list_filter = ["status", "provider"]
    search_fields = ["provider_reference", "organization__name", "owner__email"]
