from django.core.exceptions import ImproperlyConfigured

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


def scrub_sensitive_event(event, hint):
    """Remove request and user data that is unnecessary for error diagnosis."""
    event.pop("user", None)
    request = event.get("request")
    if request:
        for key in ("cookies", "data", "env", "headers", "query_string"):
            request.pop(key, None)
    return event


def traces_sampler(sampling_context):
    transaction = sampling_context.get("transaction_context", {})
    if transaction.get("name", "").rstrip("/") == "/health":
        return 0.0
    return sampling_context.get("custom_sample_rate", 0.0)


def configure_sentry(*, dsn, environment, release, traces_sample_rate):
    """Enable privacy-conscious Sentry monitoring when a DSN is configured."""
    if not dsn:
        return False
    if not 0.0 <= traces_sample_rate <= 1.0:
        raise ImproperlyConfigured(
            "SENTRY_TRACES_SAMPLE_RATE must be between 0.0 and 1.0"
        )

    def configured_traces_sampler(sampling_context):
        return traces_sampler(
            {**sampling_context, "custom_sample_rate": traces_sample_rate}
        )

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release or None,
        integrations=[DjangoIntegration(transaction_style="url")],
        send_default_pii=False,
        max_request_body_size="never",
        before_send=scrub_sensitive_event,
        traces_sampler=configured_traces_sampler,
        profiles_sample_rate=0.0,
        enable_logs=False,
    )
    return True
