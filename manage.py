#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Если DJANGO_SETTINGS_MODULE не задана, ставим dev по умолчанию
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "mgrupsite.settings"  # dev по умолчанию для локальной разработки
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Проверка: если в продакшене DEBUG=True, выдаём предупреждение
    if os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith("prod"):
        if os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes"):
            raise RuntimeError("DEBUG must be False in production!")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
