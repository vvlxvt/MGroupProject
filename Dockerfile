FROM python:3.12-slim

# --------------------------------------------
# Environment
# --------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
# ENV DJANGO_SETTINGS_MODULE не нужно здесь, его задаст сервер

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
# Проверка импорта Django настроек
# --------------------------------------------
RUN python -c "import mgrupsite.settings"

# --------------------------------------------
# Collect static files
# --------------------------------------------
RUN python manage.py collectstatic --noinput

# --------------------------------------------
# Expose port
# --------------------------------------------
EXPOSE 80

# --------------------------------------------
# Run application
# --------------------------------------------
CMD ["gunicorn", "mgrupsite.wsgi:application", \
     "--bind", "0.0.0.0:80", \
     "--workers", "3", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
