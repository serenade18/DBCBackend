from rest_framework import serializers

from apps.billing.models import Payment, Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id", "name", "slug", "description", "monthly_price", "annual_price", "currency",
            "max_vcards", "max_storage_mb", "max_team_members", "max_gallery_items",
            "max_products", "max_services", "analytics_enabled", "appointments_enabled",
            "custom_domain_enabled", "directory_enabled", "remove_branding", "priority_support",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "organization", "owner", "plan", "provider", "status",
            "trial_start", "trial_end", "current_period_start", "current_period_end",
            "cancel_at_period_end", "created_at", "updated_at",
        ]
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=["stripe", "mpesa", "sasapay"])
    organization_id = serializers.UUIDField(required=False, allow_null=True)


class CheckoutResultSerializer(serializers.Serializer):
    redirect_url = serializers.CharField(allow_null=True)
    provider_reference = serializers.CharField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "provider", "provider_reference", "amount", "currency",
            "status", "payment_method", "paid_at", "created_at",
        ]
        read_only_fields = fields
