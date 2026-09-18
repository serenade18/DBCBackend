import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Plain ASGI app for now. If/when real-time features (e.g. live in-app
# notifications) are needed, wrap this with a Channels ProtocolTypeRouter
# and add a websocket URLConf per app.
application = get_asgi_application()
