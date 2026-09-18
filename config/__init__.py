# Makes sure the Celery app is loaded whenever Django starts, so that
# shared_task-decorated functions bind to this configured app instead of
# Celery's unconfigured default (which uses AMQP/RabbitMQ defaults).
from .celery import app as celery_app

__all__ = ("celery_app",)
