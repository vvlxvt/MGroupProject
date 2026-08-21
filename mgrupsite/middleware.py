import secrets

from django.conf import settings


class ContentSecurityPolicyReportOnlyMiddleware:
    """Attach a non-blocking CSP policy to HTML responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        content_type = response.get("Content-Type", "").partition(";")[0].strip()
        if settings.CSP_REPORT_ONLY_ENABLED and content_type == "text/html":
            response["Content-Security-Policy-Report-Only"] = (
                settings.CSP_REPORT_ONLY_POLICY.format(nonce=request.csp_nonce)
            )
        return response
