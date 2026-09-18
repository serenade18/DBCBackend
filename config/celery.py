import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("dbc")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "aggregate-analytics-hourly": {
        "task": "apps.analytics.tasks.aggregate_analytics",
        "schedule": crontab(minute=5),
    },
    "check-subscriptions-daily": {
        "task": "apps.billing.tasks.check_subscriptions",
        "schedule": crontab(hour=1, minute=0),
    },
    "check-abandoned-orders-daily": {
        "task": "apps.orders.tasks.check_abandoned_orders",
        "schedule": crontab(hour=2, minute=0),
    },
    "send-appointment-reminders": {
        "task": "apps.appointments.tasks.send_appointment_reminders",
        "schedule": crontab(minute="*/15"),
    },
    "process-expired-trials-daily": {
        "task": "apps.billing.tasks.process_expired_trials",
        "schedule": crontab(hour=1, minute=30),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
