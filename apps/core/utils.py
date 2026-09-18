import hashlib

from django.conf import settings


def hash_ip(ip_address: str | None) -> str:
    """
    One-way hash of a client IP so raw IPs are never persisted or exposed to
    organization users (§25, §41), while still allowing basic abuse/analytics
    correlation on the hash.
    """
    if not ip_address:
        return ""
    salted = f"{settings.SECRET_KEY}:{ip_address}".encode()
    return hashlib.sha256(salted).hexdigest()


def get_client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_audit_event(*, actor=None, organization=None, action: str, resource_type: str,
                     resource_id: str = "", metadata: dict | None = None, request=None):
    """Write one AuditLog row. Call this from views/services at the point an
    action actually happens, not from generic middleware."""
    from apps.core.models import AuditLog

    ip_hash = hash_ip(get_client_ip(request)) if request is not None else ""
    AuditLog.objects.create(
        actor=actor,
        organization=organization,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        metadata=metadata or {},
        ip_hash=ip_hash,
    )
