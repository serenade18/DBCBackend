import logging

from celery import shared_task
from django.utils import timezone

from apps.billing.models import Subscription, SubscriptionStatus

logger = logging.getLogger("django")


@shared_task
def check_subscriptions():
    """Daily: expire subscriptions past their period end, and flip
    cancel_at_period_end subscriptions to cancelled once the period lapses."""
    now = timezone.now()
    ending = Subscription.objects.filter(
        status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE],
        current_period_end__lt=now,
    )
    for subscription in ending:
        if subscription.cancel_at_period_end:
            subscription.status = SubscriptionStatus.CANCELLED
        else:
            subscription.status = SubscriptionStatus.EXPIRED
        subscription.save(update_fields=["status"])
        logger.info("Subscription %s -> %s", subscription.id, subscription.status)

    soon = now + timezone.timedelta(days=3)
    expiring_soon = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE, current_period_end__range=(now, soon),
    )
    from apps.notifications.tasks import notify_in_app_task

    for subscription in expiring_soon:
        user = subscription.owner
        if user:
            notify_in_app_task.delay(str(user.id), "subscription_expiring", "Your subscription is expiring soon")


@shared_task
def process_expired_trials():
    now = timezone.now()
    expired_trials = Subscription.objects.filter(status=SubscriptionStatus.TRIALING, trial_end__lt=now)
    for subscription in expired_trials:
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.save(update_fields=["status"])
        logger.info("Trial expired for subscription %s", subscription.id)
