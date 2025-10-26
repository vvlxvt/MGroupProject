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
- Django 4.2
- PostgreSQL
- aiogram (Telegram bot)
- django-ckeditor, django-taggit, django-imagekit
- Bootstrap 5, WhiteNoise

## Notes
- Environment variables are required for secrets and external services (e.g., `SECRET_KEY`, `DB_*`, `TELEGRAM_*`, `GOOGLE_MAPS_API_KEY`).
- Media is stored locally by default; static files are collected into `staticfiles/`.
