import secrets

from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """Attach the configured CSP policy to HTML responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        content_type = response.get("Content-Type", "").partition(";")[0].strip()
        if content_type == "text/html":
            policy = settings.CSP_POLICY.format(nonce=request.csp_nonce)
            if settings.CSP_ENFORCE_ENABLED:
                response["Content-Security-Policy"] = policy
            elif settings.CSP_REPORT_ONLY_ENABLED:
                response["Content-Security-Policy-Report-Only"] = policy
        return response
