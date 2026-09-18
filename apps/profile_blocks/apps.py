from django.apps import AppConfig


class ProfileBlocksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profile_blocks"
    label = "profile_blocks"

    def ready(self):
        from apps.profile_blocks import signals  # noqa: F401
