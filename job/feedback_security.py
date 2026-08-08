import time

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.utils.crypto import salted_hmac


FORM_TOKEN_MAX_AGE = 2 * 60 * 60
FORM_MIN_FILL_SECONDS = 2


def create_form_token(form_name):
    return signing.dumps(
        {"form": form_name, "issued_at": time.time()},
        salt="feedback-form",
        compress=True,
    )


def validate_form_token(token, form_name):
    try:
        payload = signing.loads(
            token,
            salt="feedback-form",
            max_age=FORM_TOKEN_MAX_AGE,
        )
    except (signing.BadSignature, signing.SignatureExpired):
        return False

    issued_at = payload.get("issued_at")
    if payload.get("form") != form_name or not isinstance(issued_at, (int, float)):
        return False
    return time.time() - issued_at >= FORM_MIN_FILL_SECONDS


def get_client_identifier(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    client_ip = forwarded_for.split(",", 1)[0].strip()
    return client_ip or request.META.get("REMOTE_ADDR", "unknown")


def rate_limit_exceeded(scope, identifier, limit, window_seconds):
    digest = salted_hmac(
        "feedback-rate-limit",
        str(identifier).strip().lower(),
        secret=settings.SECRET_KEY,
    ).hexdigest()
    cache_key = f"feedback-rate:{scope}:{digest}"

    current = cache.get(cache_key, 0)
    if current >= limit:
        return True

    if current:
        try:
            cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, current + 1, window_seconds)
    else:
        cache.set(cache_key, 1, window_seconds)
    return False
