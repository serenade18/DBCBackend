from django.db import connection
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.serializers import ComponentHealthSerializer, HealthSerializer

try:
    import redis as redis_lib
    from django.conf import settings
except ImportError:  # pragma: no cover
    redis_lib = None


def _check_database() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except OperationalError:
        return False


def _check_redis() -> bool:
    if redis_lib is None:
        return False
    try:
        client = redis_lib.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        return client.ping()
    except Exception:
        return False


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=HealthSerializer)
    def get(self, request):
        db_ok = _check_database()
        redis_ok = _check_redis()
        overall = "healthy" if db_ok and redis_ok else "unhealthy"
        status_code = 200 if overall == "healthy" else 503
        return Response(
            {
                "status": overall,
                "database": "healthy" if db_ok else "unhealthy",
                "redis": "healthy" if redis_ok else "unhealthy",
            },
            status=status_code,
        )


class DatabaseHealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=ComponentHealthSerializer)
    def get(self, request):
        ok = _check_database()
        return Response({"database": "healthy" if ok else "unhealthy"}, status=200 if ok else 503)


class RedisHealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=ComponentHealthSerializer)
    def get(self, request):
        ok = _check_redis()
        return Response({"redis": "healthy" if ok else "unhealthy"}, status=200 if ok else 503)
