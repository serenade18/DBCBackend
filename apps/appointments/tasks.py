import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentStatus

logger = logging.getLogger("django")

REMINDER_WINDOW_HOURS = 24


@shared_task
def send_appointment_reminders():
    """Runs every 15 min (see config/celery.py beat schedule): reminds
    customers of confirmed appointments starting in ~24h, once."""
    now = timezone.now()
    window_start = now + timedelta(hours=REMINDER_WINDOW_HOURS) - timedelta(minutes=15)
    window_end = now + timedelta(hours=REMINDER_WINDOW_HOURS)

    upcoming = Appointment.objects.filter(
        status=AppointmentStatus.CONFIRMED, reminder_sent_at__isnull=True,
    ).select_related("vcard", "service")

    from apps.notifications.email import email_table, send_email, wrap_email

    for appointment in upcoming:
        naive_start = timezone.datetime.combine(appointment.date, appointment.start_time)
        starts_at = timezone.make_aware(naive_start) if timezone.is_naive(naive_start) else naive_start

        if not (window_start <= starts_at <= window_end):
            continue

        text = (
            f"This is a reminder for your {appointment.service.name} appointment on "
            f"{appointment.date} at {appointment.start_time}."
        )
        html = wrap_email(
            title="Appointment reminder",
            body_html=(
                "<p>This is a reminder for your upcoming appointment.</p>"
                + email_table([
                    ("Service", appointment.service.name),
                    ("Date", str(appointment.date)),
                    ("Time", str(appointment.start_time)),
                ])
            ),
        )
        send_email(
            to=appointment.customer_email,
            subject=f"Reminder: {appointment.service.name} tomorrow",
            body=text,
            html_body=html,
        )
        appointment.reminder_sent_at = now
        appointment.save(update_fields=["reminder_sent_at"])
        logger.info("Sent reminder for appointment %s", appointment.id)
