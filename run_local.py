"""Run the Django WSGI application for local development."""

import os

from django.core.servers.basehttp import run
from django.core.wsgi import get_wsgi_application


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mgrupsite.settings")
    run("127.0.0.1", 8000, get_wsgi_application(), threading=True)
