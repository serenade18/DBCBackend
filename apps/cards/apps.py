from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cards"
    label = "cards"

    def ready(self):
        from apps.cards import signals  # noqa: F401
