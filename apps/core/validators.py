from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE_MB = 10
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}


def validate_image_file(file) -> None:
    """Hard cap + MIME check applied to every image upload (§41, §44),
    independent of plan storage quotas (see EntitlementService.can_upload
    for the plan-level check, applied separately where it matters most)."""
    if file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Image must be smaller than {MAX_IMAGE_SIZE_MB}MB.")

    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValidationError("Unsupported image type. Use JPEG, PNG, WEBP, or SVG.")
