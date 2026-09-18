import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.orders.models import Order, OrderStatus

logger = logging.getLogger("django")

ABANDONED_AFTER_HOURS = 48


@shared_task
def check_abandoned_orders():
    """Daily: flags/cancels orders stuck in pending_payment (§48)."""
    cutoff = timezone.now() - timedelta(hours=ABANDONED_AFTER_HOURS)
    abandoned = Order.objects.filter(status=OrderStatus.PENDING_PAYMENT, created_at__lt=cutoff)

    from apps.notifications.tasks import notify_in_app_task

    for order in abandoned:
        if order.customer_id:
            notify_in_app_task.delay(
                str(order.customer_id), "order_received",
                f"Your order {order.order_number} is awaiting payment",
            )
        logger.info("Order %s flagged as abandoned (pending_payment > %dh)", order.order_number, ABANDONED_AFTER_HOURS)
