from celery import shared_task
from django.conf import settings

from apps.notifications.email import (
    email_button,
    email_table,
    password_reset_url,
    send_email,
    verification_email_url,
    wrap_email,
)
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
    name = user.first_name or "there"
    text = (
        f"Hi {name},\n\nPlease verify your email: {url}\n\nIf you didn't sign up, ignore this email."
    )
    html = wrap_email(
        title="Verify your email",
        body_html=f"<p>Hi {name},</p><p>Confirm your email address to activate your DBC account.</p>",
        cta_html=email_button("Verify email", url),
    )
    send_email(to=user.email, subject="Verify your email", body=text, html_body=html)


@shared_task
def send_password_reset_email(user_id, uid, token):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(id=user_id).first()
    if not user:
        return
    url = password_reset_url(uid, token)
    name = user.first_name or "there"
    text = (
        f"Hi {name},\n\nReset your password: {url}\n\nIf you didn't request this, ignore this email."
    )
    html = wrap_email(
        title="Reset your password",
        body_html=(
            f"<p>Hi {name},</p>"
            "<p>We received a request to reset your DBC password. Click below to choose a new one.</p>"
            "<p>If you didn't request this, you can safely ignore this email — your password won't change.</p>"
        ),
        cta_html=email_button("Reset password", url),
    )
    send_email(to=user.email, subject="Reset your password", body=text, html_body=html)


@shared_task
def send_welcome_email(user_id):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(id=user_id).first()
    if not user:
        return
    name = user.first_name or "there"
    dashboard_url = f"{settings.FRONTEND_URL}/app"
    text = f"Hi {name}, welcome aboard.\n\nGet started: {dashboard_url}"
    html = wrap_email(
        title=f"Welcome, {name}",
        body_html="<p>Thanks for joining DBC. Create your first card and share it in minutes.</p>",
        cta_html=email_button("Go to dashboard", dashboard_url),
    )
    send_email(to=user.email, subject="Welcome to DBC", body=text, html_body=html)
    notify_in_app(user_id=user_id, type="welcome", title="Welcome to the platform!")


@shared_task
def send_team_invitation_email(member_id):
    from apps.organizations.models import OrganizationMember

    member = OrganizationMember.objects.filter(id=member_id).select_related("organization", "user").first()
    if not member:
        return
    url = f"{settings.FRONTEND_URL}/invitations/{member.id}"
    org_name = member.organization.name
    text = f"You've been invited to join {org_name} as {member.role}. Accept here: {url}"
    html = wrap_email(
        title="You've been invited",
        body_html=(
            f"<p>You've been invited to join <strong>{org_name}</strong> on DBC as "
            f"<strong>{member.role}</strong>.</p>"
        ),
        cta_html=email_button("Accept invitation", url),
    )
    send_email(to=member.user.email, subject=f"You've been invited to join {org_name}", body=text, html_body=html)
    notify_in_app(
        user_id=member.user_id,
        type="team_invitation",
        title=f"Invitation to join {org_name}",
        link_url=url,
    )


@shared_task
def notify_new_enquiry(enquiry_id):
    from apps.enquiries.models import Enquiry

    enquiry = Enquiry.objects.filter(id=enquiry_id).select_related("vcard", "vcard__owner").first()
    if not enquiry:
        return
    recipient = enquiry.vcard.assigned_user or enquiry.vcard.owner
    url = f"{settings.FRONTEND_URL}/app/enquiries?vcard={enquiry.vcard_id}"
    text = f"{enquiry.name} ({enquiry.email}) sent:\n\n{enquiry.message}\n\nView it: {url}"
    html = wrap_email(
        title=f"New enquiry on {enquiry.vcard.display_name}",
        body_html=(
            email_table([("From", enquiry.name), ("Email", enquiry.email)])
            + f"<p>{enquiry.message}</p>"
        ),
        cta_html=email_button("View enquiry", url),
    )
    send_email(
        to=recipient.email,
        subject=f"New enquiry on {enquiry.vcard.display_name}",
        body=text,
        html_body=html,
    )
    notify_in_app(
        user_id=recipient.id,
        type="new_enquiry",
        title=f"New enquiry from {enquiry.name}",
        body=enquiry.message[:200],
        link_url=url,
    )


@shared_task
def notify_new_appointment(appointment_id):
    from apps.appointments.models import Appointment

    appointment = Appointment.objects.filter(id=appointment_id).select_related("vcard", "vcard__owner", "service").first()
    if not appointment:
        return
    recipient = appointment.vcard.assigned_user or appointment.vcard.owner
    url = f"{settings.FRONTEND_URL}/app/appointments?vcard={appointment.vcard_id}"
    text = (
        f"{appointment.customer_name} booked {appointment.service.name} on "
        f"{appointment.date} at {appointment.start_time}.\n\nView it: {url}"
    )
    html = wrap_email(
        title="New appointment booked",
        body_html=email_table([
            ("Customer", appointment.customer_name),
            ("Service", appointment.service.name),
            ("Date", str(appointment.date)),
            ("Time", str(appointment.start_time)),
        ]),
        cta_html=email_button("View appointment", url),
    )
    send_email(
        to=recipient.email,
        subject=f"New appointment booked: {appointment.customer_name}",
        body=text,
        html_body=html,
    )
    notify_in_app(
        user_id=recipient.id,
        type="new_appointment",
        title=f"New appointment with {appointment.customer_name}",
        link_url=url,
    )
