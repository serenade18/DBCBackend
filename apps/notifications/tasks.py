from celery import shared_task
from django.conf import settings

from apps.notifications.email import password_reset_url, send_email, verification_email_url
from apps.notifications.sms import send_sms


def notify_in_app(*, user_id, type, title, body="", link_url="", metadata=None):
    """Create an in-app Notification row. Not a Celery task itself so it can
    be called synchronously from within other tasks without a nested
    dispatch; callers that want it async should wrap it in notify_in_app_task."""
    from apps.notifications.models import Notification

    return Notification.objects.create(
        user_id=user_id, type=type, title=title, body=body, link_url=link_url, metadata=metadata or {}
    )


@shared_task
def notify_in_app_task(user_id, type, title, body="", link_url="", metadata=None):
    notify_in_app(user_id=user_id, type=type, title=title, body=body, link_url=link_url, metadata=metadata)


@shared_task
def send_email_task(to, subject, body, html_body=None):
    return send_email(to=to, subject=subject, body=body, html_body=html_body)


@shared_task
def send_sms_task(to, message):
    return send_sms(to=to, message=message)


@shared_task
def send_verification_email(user_id, uid, token):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(id=user_id).first()
    if not user:
        return
    url = verification_email_url(uid, token)
    send_email(
        to=user.email,
        subject="Verify your email",
        body=f"Hi {user.first_name or ''},\n\nPlease verify your email: {url}\n\nIf you didn't sign up, ignore this email.",
    )


@shared_task
def send_password_reset_email(user_id, uid, token):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(id=user_id).first()
    if not user:
        return
    url = password_reset_url(uid, token)
    send_email(
        to=user.email,
        subject="Reset your password",
        body=f"Hi {user.first_name or ''},\n\nReset your password: {url}\n\nIf you didn't request this, ignore this email.",
    )


@shared_task
def send_welcome_email(user_id):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(id=user_id).first()
    if not user:
        return
    send_email(to=user.email, subject="Welcome!", body=f"Hi {user.first_name or ''}, welcome aboard.")
    notify_in_app(user_id=user_id, type="welcome", title="Welcome to the platform!")


@shared_task
def send_team_invitation_email(member_id):
    from apps.organizations.models import OrganizationMember

    member = OrganizationMember.objects.filter(id=member_id).select_related("organization", "user").first()
    if not member:
        return
    url = f"{settings.FRONTEND_URL}/invitations/{member.id}"
    send_email(
        to=member.user.email,
        subject=f"You've been invited to join {member.organization.name}",
        body=f"You've been invited to join {member.organization.name} as {member.role}. Accept here: {url}",
    )
    notify_in_app(
        user_id=member.user_id,
        type="team_invitation",
        title=f"Invitation to join {member.organization.name}",
        link_url=url,
    )


@shared_task
def notify_new_enquiry(enquiry_id):
    from apps.enquiries.models import Enquiry

    enquiry = Enquiry.objects.filter(id=enquiry_id).select_related("vcard", "vcard__owner").first()
    if not enquiry:
        return
    recipient = enquiry.vcard.assigned_user or enquiry.vcard.owner
    send_email(
        to=recipient.email,
        subject=f"New enquiry on {enquiry.vcard.display_name}",
        body=f"{enquiry.name} ({enquiry.email}) sent:\n\n{enquiry.message}",
    )
    notify_in_app(
        user_id=recipient.id,
        type="new_enquiry",
        title=f"New enquiry from {enquiry.name}",
        body=enquiry.message[:200],
        link_url=f"{settings.FRONTEND_URL}/enquiries/{enquiry.id}",
    )


@shared_task
def notify_new_appointment(appointment_id):
    from apps.appointments.models import Appointment

    appointment = Appointment.objects.filter(id=appointment_id).select_related("vcard", "vcard__owner", "service").first()
    if not appointment:
        return
    recipient = appointment.vcard.assigned_user or appointment.vcard.owner
    send_email(
        to=recipient.email,
        subject=f"New appointment booked: {appointment.customer_name}",
        body=f"{appointment.customer_name} booked {appointment.service.name} on {appointment.date} at {appointment.start_time}.",
    )
    notify_in_app(
        user_id=recipient.id,
        type="new_appointment",
        title=f"New appointment with {appointment.customer_name}",
    )
