import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("django")


def send_email(*, to: str, subject: str, body: str, html_body: str | None = None) -> bool:
    """Thin wrapper around the configured email sender. Swap EMAIL_BACKEND /
    add a provider-specific backend without touching callers.

    When RESEND_API_KEY is set, sends synchronously via the Resend API (a
    plain HTTP call — no SMTP, no Celery worker required). Otherwise falls
    back to Django's EMAIL_BACKEND (console backend by default in dev)."""
    if settings.RESEND_API_KEY:
        return _send_via_resend(to=to, subject=subject, body=body, html_body=html_body)

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
            html_message=html_body,
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Failed to send email to %s (%s)", to, subject)
        return False


def _send_via_resend(*, to: str, subject: str, body: str, html_body: str | None) -> bool:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    try:
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "text": body,
            **({"html": html_body} if html_body else {}),
        })
        return True
    except Exception:
        logger.exception("Failed to send email via Resend to %s (%s)", to, subject)
        return False


def verification_email_url(uid: str, token: str) -> str:
    return f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={token}"


def password_reset_url(uid: str, token: str) -> str:
    return f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"


# ---------------------------------------------------------------------------
# Shared HTML shell — every notification email renders through this so they
# stay visually consistent with the dashboard's neutral/rounded look.
# ---------------------------------------------------------------------------

def wrap_email(title: str, body_html: str, cta_html: str = "") -> str:
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f4f5;font-family:Helvetica,Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:32px 0;">
        <tr><td align="center">
          <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e4e4e7;">
            <tr><td style="padding:28px 40px;border-bottom:1px solid #e4e4e7;">
              <table cellpadding="0" cellspacing="0"><tr>
                <td style="width:28px;height:28px;background:#111827;border-radius:8px;text-align:center;vertical-align:middle;">
                  <span style="color:#ffffff;font-size:14px;font-weight:700;font-family:Helvetica,Arial,sans-serif;">D</span>
                </td>
                <td style="padding-left:8px;font-size:16px;font-weight:600;color:#111827;">DBC</td>
              </tr></table>
            </td></tr>
            <tr><td style="padding:36px 40px;color:#111827;font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:1.6;">
              <h1 style="font-size:20px;font-weight:600;color:#111827;margin:0 0 16px;">{title}</h1>
              {body_html}
              {cta_html}
            </td></tr>
            <tr><td style="padding:20px 40px;background:#fafafa;color:#71717a;font-size:12px;font-family:Helvetica,Arial,sans-serif;text-align:center;">
              You're receiving this email because you have an account with DBC.
            </td></tr>
          </table>
        </td></tr>
      </table>
    </body></html>
    """


def email_button(label: str, url: str) -> str:
    return f"""
    <p style="margin:26px 0 14px;">
      <a href="{url}" style="display:inline-block;background:#111827;color:#ffffff;text-decoration:none;
         padding:11px 24px;border-radius:8px;font-family:Helvetica,Arial,sans-serif;font-size:14px;
         font-weight:500;">{label}</a>
    </p>
    <p style="font-size:12px;color:#71717a;word-break:break-all;margin:0;">
      Or copy this link: <br/>{url}
    </p>
    """


def email_table(rows: list[tuple[str, str]]) -> str:
    """A compact label/value table for structured details (enquiry, booking, …)."""
    cells = "".join(
        f"<tr><td style='padding:5px 16px 5px 0;color:#71717a;'>{label}</td>"
        f"<td style='padding:5px 0;'><strong>{value}</strong></td></tr>"
        for label, value in rows
    )
    return f"<table style='margin:18px 0;font-size:14px;'>{cells}</table>"
