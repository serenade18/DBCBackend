from rest_framework import serializers

from apps.orders.models import Order, OrderItem, PhysicalCardProduct, ShippingAddress, ShippingEvent


class PhysicalCardProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalCardProduct
        fields = ["id", "name", "material", "description", "price", "currency", "image"]
        read_only_fields = fields


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            "full_name", "company", "phone", "address_line_1", "address_line_2",
            "city", "state", "postal_code", "country",
        ]


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    vcard_id = serializers.UUIDField(required=False, allow_null=True)


class OrderItemSerializer(serializers.ModelSerializer):
    product = PhysicalCardProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price", "vcard"]
        read_only_fields = fields


class ShippingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingEvent
        fields = ["id", "status", "description", "tracking_number", "timestamp"]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    shipping_events = ShippingEventSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "organization", "customer", "order_number", "status", "payment_status",
            "subtotal", "shipping_fee", "tax", "total", "currency",
            "shipping_address", "items", "shipping_events", "created_at", "updated_at",
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField(required=False, allow_null=True)
    items = OrderItemInputSerializer(many=True)
    shipping_address = ShippingAddressSerializer()
    provider = serializers.ChoiceField(choices=["stripe", "mpesa", "sasapay"])


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    tracking_number = serializers.CharField(required=False, allow_blank=True, write_only=True)
    description = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Order
        fields = ["status", "tracking_number", "description"]
