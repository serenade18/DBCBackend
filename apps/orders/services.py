from decimal import Decimal

from django.db import transaction

from apps.orders.models import Order, OrderItem, PhysicalCardProduct, ShippingAddress, ShippingEvent

FLAT_SHIPPING_FEE = Decimal("5.00")
TAX_RATE = Decimal("0.00")  # TODO: wire real per-country tax rules once launch markets are set


class OrderValidationError(Exception):
    pass


@transaction.atomic
def create_order(*, customer, organization, items_data, shipping_address_data, currency="USD"):
    if not items_data:
        raise OrderValidationError("An order must contain at least one item.")

    shipping_address = ShippingAddress.objects.create(**shipping_address_data)
    order = Order.objects.create(
        customer=customer, organization=organization, shipping_address=shipping_address,
        currency=currency, shipping_fee=FLAT_SHIPPING_FEE,
    )

    subtotal = Decimal("0")
    for item_data in items_data:
        product = PhysicalCardProduct.objects.filter(id=item_data["product_id"], is_active=True).first()
        if not product:
            raise OrderValidationError(f"Product {item_data['product_id']} not found or inactive.")
        quantity = item_data.get("quantity", 1)
        OrderItem.objects.create(
            order=order, product=product, quantity=quantity, unit_price=product.price,
            vcard_id=item_data.get("vcard_id"),
        )
        subtotal += product.price * quantity

    order.subtotal = subtotal
    order.tax = subtotal * TAX_RATE
    order.total = order.subtotal + order.shipping_fee + order.tax
    order.save(update_fields=["subtotal", "tax", "total"])

    ShippingEvent.objects.create(order=order, status=order.status, description="Order created.")
    return order


def advance_status(order: Order, new_status: str, *, description: str = "", tracking_number: str = ""):
    order.status = new_status
    order.save(update_fields=["status"])
    ShippingEvent.objects.create(
        order=order, status=new_status, description=description, tracking_number=tracking_number,
    )

    from apps.notifications.tasks import notify_in_app_task

    if order.customer:
        event_map = {"shipped": "order_shipped", "delivered": "order_delivered"}
        if new_status in event_map:
            notify_in_app_task.delay(str(order.customer_id), event_map[new_status], f"Order {order.order_number} {new_status}")
