# MGroup Project — Django Web Application

## Description
A Django-based company website with a services catalog, articles, a project
portfolio, protected feedback forms, SEO metadata, and asynchronous Telegram
notifications.

## Features
- **Home and Services**
- **Articles (Blog)**
  - Rich text content via TipTap
  - Tagging support (django-taggit)
  - Article detail pages with clean slugs
- **Projects (Portfolio)**
  - Project pages with descriptions
  - Photo gallery with generated thumbnails
  - Optional geolocation (lat/lng) for map integrations
- **Contact and Feedback**
  - Contact page and vacancies page
  - Question and vacancy forms protected by honeypots, rate limits, signed form
    tokens, reCAPTCHA, and explicit consent
- **Telegram Notifications**
  - Feedback is persisted before delivery
  - A background worker sends queued questions and vacancy responses
  - Failed deliveries can be retried without resubmitting a form
- **Feeds and SEO**
  - Latest posts RSS/Atom feed
  - Sitemaps and robots.txt
- **Admin/CMS**
  - Django admin with image previews and thumbnails
  - Media uploads and static file management
- **Front-end**
  - Bootstrap 5 styling
- **Infrastructure**
  - PostgreSQL database in development and production
  - Media stored in Yandex Object Storage
  - Static assets served with WhiteNoise
  - Environment-driven configuration
  - Production database and media backup commands

## Tech Stack
- Django 5.2 LTS
- PostgreSQL
- django-tiptap-editor, django-taggit, django-imagekit
- Bootstrap 5, WhiteNoise

## Notes
- Environment variables are required for secrets and external services. Never
  commit `.env` files, database dumps, static access keys, or Telegram tokens.
- Development uses `DEV_DB_*`; production uses `PROD_DB_*`.
- Development media is stored locally. Production media is stored in the
  `mgroup` Yandex Object Storage bucket.
- Production static files are collected under `/data/static` and served through
  WhiteNoise.

### Production domains

Production host validation and absolute URLs are configured through environment
variables:

- `APP_HOSTS` — comma-separated hostnames without a scheme;
- `CSRF_TRUSTED_ORIGINS` — comma-separated HTTPS origins;
- `CANONICAL_BASE_URL` — the single public URL used for canonical and structured
  data links;
- `ALLOWED_RECAPTCHA_HOSTS` — comma-separated hostnames accepted in reCAPTCHA
  verification responses;
- `WEBHOOK_HOST` — optional external webhook base URL; defaults to
  `CANONICAL_BASE_URL`.

Before DNS and TLS for `мгрупп.рф` are ready, keep the Amvera URL canonical. For
the final domain switch use:

```text
APP_HOSTS=mgroup-vvlxvt.amvera.io,xn--c1arkads.xn--p1ai
CSRF_TRUSTED_ORIGINS=https://mgroup-vvlxvt.amvera.io,https://xn--c1arkads.xn--p1ai
CANONICAL_BASE_URL=https://xn--c1arkads.xn--p1ai
ALLOWED_RECAPTCHA_HOSTS=mgroup-vvlxvt.amvera.io,xn--c1arkads.xn--p1ai
```

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

Required backup variables:

- `BACKUP_S3_BUCKET` — a separate private bucket, currently
  `mgroup-vvlxvt-backups`;
- `BACKUP_S3_ACCESS_KEY_ID` and `BACKUP_S3_SECRET_ACCESS_KEY` — preferably a
  dedicated service-account key. The `mgroup-backup` account has
  `storage.viewer` on the `mgroup` media bucket and `storage.uploader` on the
  backup bucket. Delete permission and KMS permissions are not required;
- the existing `PROD_DB_*` variables used by Django.

Optional variables are `BACKUP_S3_PREFIX`, `BACKUP_S3_ENDPOINT_URL`,
`BACKUP_DATABASE_TIMEOUT_SECONDS`, and `BACKUP_PGSSLMODE`.

The command is ready for manual or external scheduled execution. A permanently
running Amvera Cron Job is intentionally not required. The scheduler must run
the following command in an environment containing the production variables:

```bash
python manage.py backup_production
```

The command exits with a non-zero status on a failed dump, archive validation,
copy, size check, or checksum check. A successful log contains both
`PostgreSQL backup uploaded` and `Object Storage backup completed`.

Do not delete the production PostgreSQL service until a recent archive has been
restored successfully into a separate verification database.

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
