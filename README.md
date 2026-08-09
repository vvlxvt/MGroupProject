# MGroup Project — Django Web Application

## Description
A Django-based website that powers a content-driven company site with a services catalog, articles, and a portfolio of projects. It includes media management, tagging, an RSS feed, SEO assets, and a Telegram integration for user interactions and callbacks.

## Features
- **Home and Services**
- **Articles (Blog)**
  - Rich text content via CKEditor
  - Tagging support (django-taggit)
  - Article detail pages with clean slugs
- **Projects (Portfolio)**
  - Project pages with descriptions
  - Photo gallery with generated thumbnails
  - Optional geolocation (lat/lng) for map integrations
- **Contact and Feedback**
  - Contact page and vacancies page
  - Submit question form endpoint
- **Telegram Integration**
  - Telegram bot (aiogram) with webhook support
  - Telegram Login/Callback endpoint and user profile linking
  - User questions with optional attached photos
- **Feeds and SEO**
  - Latest posts RSS/Atom feed
  - Sitemaps and robots.txt
- **Admin/CMS**
  - Django admin with image previews and thumbnails
  - Media uploads and static file management
- **Front-end**
  - Bootstrap 5 styling
- **Infrastructure**
  - PostgreSQL database
  - Static assets served with WhiteNoise
  - Environment-driven configuration (.env)

## Tech Stack
- Django 5.2 LTS
- PostgreSQL
- aiogram (Telegram bot)
- django-tiptap-editor, django-taggit, django-imagekit
- Bootstrap 5, WhiteNoise

## Notes
- Environment variables are required for secrets and external services (e.g., `SECRET_KEY`, `DB_*`, `TELEGRAM_*`, `GOOGLE_MAPS_API_KEY`).
- Media is stored locally by default; static files are collected into `staticfiles/`.

## Telegram notification worker

Contact questions and vacancy responses are saved during the web request and
delivered to Telegram by the notification worker. On Amvera it starts alongside
Gunicorn. For a one-off manual run use:

```bash
python manage.py process_feedback_notifications --limit 50
```

To retry notifications previously marked as failed:

```bash
python manage.py process_feedback_notifications --limit 50 --retry-failed
```

## Production backups

PostgreSQL backups are created with `pg_dump`, validated with `pg_restore`, and
uploaded to a private Object Storage bucket that must be separate from the
public media bucket. Media objects are copied incrementally to immutable,
content-addressed keys, followed by a point-in-time JSON manifest:

```bash
python manage.py backup_production
```

Required production variables:

- `BACKUP_S3_BUCKET` — a separate private bucket, for example `mgroup-backups`;
- `BACKUP_S3_ACCESS_KEY_ID` and `BACKUP_S3_SECRET_ACCESS_KEY` — preferably a
  dedicated service-account key. It needs read access to the `mgroup` media
  bucket and read/write access to the backup bucket. Delete permission is not
  required.

Optional variables are `BACKUP_S3_PREFIX`, `BACKUP_S3_ENDPOINT_URL`,
`BACKUP_DATABASE_TIMEOUT_SECONDS`, and `BACKUP_PGSSLMODE`. Configure an Amvera
Cron Job to execute the command daily. Amvera schedules use UTC. A daily run at
02:00 UTC uses the schedule `0 0 2 * * ?` and the command:

```bash
python manage.py backup_production
```

The command exits with a non-zero status on a failed dump, archive validation,
copy, size check, or checksum check. A successful log contains both
`PostgreSQL backup uploaded` and `Object Storage backup completed`.

### Backup layout

- PostgreSQL archives:
  `<prefix>/postgresql/YYYY/MM/DD/database-<UTC timestamp>.dump`;
- immutable media versions:
  `<prefix>/object-storage/objects/<hash prefix>/<content identity>`;
- point-in-time media manifests:
  `<prefix>/object-storage/manifests/YYYY/MM/DD/manifest-<UTC timestamp>.json`.

Never configure `BACKUP_S3_BUCKET` with the same name as
`AWS_STORAGE_BUCKET_NAME`; the command rejects this configuration.

### Restore drill

At least monthly, download a recent database archive and restore it into a new,
empty verification database — never over the production database:

```bash
createdb mgroup_restore_test
pg_restore --no-owner --no-acl --dbname=mgroup_restore_test database.dump
```

Run `python manage.py check` against that database and compare key object counts.
For media, select a manifest, verify that every `backup_key` exists in the
backup bucket, and restore selected objects to a temporary prefix before copying
anything back to the production bucket.

For the media bucket, enable Object Storage versioning and add lifecycle rules
for noncurrent versions. Versioning is irreversible (it can only be suspended),
so it is intentionally configured in Yandex Cloud rather than at application
startup.

# Temporary UI assets

The experimental hero image `hero-features-placeholder.jpg` is based on
“Ouvriers sur un chantier de construction” by Minette Lontsie, licensed under
CC BY-SA 4.0. Source: https://commons.wikimedia.org/wiki/File:Ouvriers_sur_un_chantier_de_construction.jpg
