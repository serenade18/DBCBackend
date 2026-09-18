from datetime import datetime, timedelta

from apps.appointments.models import Appointment, AppointmentStatus, AvailabilityRule


class SlotUnavailableError(Exception):
    pass


def get_available_slots(vcard, service, date):
    """Returns a list of (start_time, end_time) tuples open for booking on
    `date`, derived from the vcard's AvailabilityRule for that weekday minus
    already-booked (pending/confirmed) appointments."""
    weekday = date.weekday()
    rules = AvailabilityRule.objects.filter(vcard=vcard, weekday=weekday)
    if not rules.exists():
        return []

    booked = Appointment.objects.filter(
        vcard=vcard, date=date, status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED],
    ).values_list("start_time", "end_time")

    duration = timedelta(minutes=service.duration_minutes)
    slots = []
    for rule in rules:
        cursor = datetime.combine(date, rule.start_time)
        end_of_rule = datetime.combine(date, rule.end_time)
        while cursor + duration <= end_of_rule:
            slot_start, slot_end = cursor.time(), (cursor + duration).time()
            overlaps = any(slot_start < b_end and slot_end > b_start for b_start, b_end in booked)
            if not overlaps:
                slots.append((slot_start, slot_end))
            cursor += duration
    return slots


def book_appointment(*, vcard, service, customer_name, customer_email, customer_phone, date, start_time, notes=""):
    duration = timedelta(minutes=service.duration_minutes)
    end_time = (datetime.combine(date, start_time) + duration).time()

    available = {slot_start for slot_start, _ in get_available_slots(vcard, service, date)}
    if start_time not in available:
        raise SlotUnavailableError("That time slot is no longer available.")

    appointment = Appointment.objects.create(
        vcard=vcard, service=service, customer_name=customer_name, customer_email=customer_email,
        customer_phone=customer_phone, date=date, start_time=start_time, end_time=end_time, notes=notes,
    )

    from apps.notifications.tasks import notify_new_appointment

    notify_new_appointment.delay(str(appointment.id))
    return appointment
