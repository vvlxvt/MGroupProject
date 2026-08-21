import logging

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe


logger = logging.getLogger(__name__)


@require_safe
def health_check(request):
    """Report application readiness without exposing internal diagnostics."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        logger.error(
            "Health check failed: dependency=database error_type=%s",
            type(exc).__name__,
        )
        response = JsonResponse({"status": "unavailable"}, status=503)
    else:
        response = JsonResponse({"status": "ok"})

    response["Cache-Control"] = "no-store"
    return response
