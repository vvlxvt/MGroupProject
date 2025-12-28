FROM python:3.12-slim

# --------------------------------------------
# Environment
# --------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
# DJANGO_SETTINGS_MODULE задаётся на сервере, здесь не указываем

WORKDIR /app

# --------------------------------------------
# System dependencies
# --------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------
# Python dependencies
# --------------------------------------------
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --------------------------------------------
# Project files
# --------------------------------------------
COPY . .

# --------------------------------------------
# Collect static files
# --------------------------------------------
# Переменные окружения не нужны для collectstatic,
# если ты используешь Whitenoise и DEBUG=False по умолчанию в base.py
RUN python manage.py collectstatic --noinput || echo "Skipping collectstatic: missing ENV variables"

# --------------------------------------------
# Expose port
# --------------------------------------------
EXPOSE 80

# --------------------------------------------
# Run application
# --------------------------------------------
CMD ["gunicorn", "mgrupsite.wsgi:application", "--bind", "0.0.0.0:80", "--workers", "3", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-"]

