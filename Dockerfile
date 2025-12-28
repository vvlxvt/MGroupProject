FROM python:3.12-slim

# --------------------------------------------
# Environment
# --------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --------------------------------------------
# Working directory
# --------------------------------------------
WORKDIR /app

# --------------------------------------------
# System deps (минимум)
# --------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------
# Python deps
# --------------------------------------------
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --------------------------------------------
# Project files
# --------------------------------------------
COPY . .

# --------------------------------------------
# Static files (Whitenoise)
# --------------------------------------------
RUN python manage.py collectstatic --noinput

# --------------------------------------------
# Amvera expects port 80
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
