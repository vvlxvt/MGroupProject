import logging
import time
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import close_old_connections

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows development fallback
    fcntl = None


logger = logging.getLogger(__name__)
BACKUP_SUCCESS_CACHE_KEY = "production-backup:last-success"


class Command(BaseCommand):
    help = "Continuously process queued feedback notifications"

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=60)
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        interval = max(options["interval"], 10)
        backup_retry_seconds = max(settings.PRODUCTION_BACKUP_RETRY_SECONDS, 60)
        next_backup_attempt = time.time()
        first_iteration = True
        while True:
            close_old_connections()
            try:
                call_command(
                    "process_feedback_notifications",
                    limit=options["limit"],
                    retry_failed=first_iteration,
                )
            except Exception:
                logger.exception("Feedback worker iteration failed")
            finally:
                close_old_connections()

            now = time.time()
            if settings.PRODUCTION_BACKUP_ENABLED and now >= next_backup_attempt:
                next_backup_attempt = self._run_backup_if_due(
                    now,
                    retry_seconds=backup_retry_seconds,
                )

            if options["once"]:
                return
            first_iteration = False
            time.sleep(interval)

    def _run_backup_if_due(self, now, retry_seconds):
        backup_interval = max(settings.PRODUCTION_BACKUP_INTERVAL_SECONDS, 60)
        last_success = cache.get(BACKUP_SUCCESS_CACHE_KEY)
        if isinstance(last_success, (int, float)):
            due_at = last_success + backup_interval
            if due_at > now:
                return due_at

        with self._backup_lock() as acquired:
            if not acquired:
                logger.info("Production backup already runs in another worker")
                return now + retry_seconds

            # Re-check after acquiring the process lock because another worker
            # may have completed the backup while this worker was waiting.
            last_success = cache.get(BACKUP_SUCCESS_CACHE_KEY)
            if isinstance(last_success, (int, float)):
                due_at = last_success + backup_interval
                if due_at > now:
                    return due_at

            logger.info("Starting scheduled production backup")
            close_old_connections()
            try:
                call_command("backup_production")
            except Exception:
                logger.exception("Scheduled production backup failed")
                return time.time() + retry_seconds
            finally:
                close_old_connections()

            completed_at = time.time()
            cache.set(BACKUP_SUCCESS_CACHE_KEY, completed_at, timeout=None)
            logger.info("Scheduled production backup completed")
            return completed_at + backup_interval

    @staticmethod
    @contextmanager
    def _backup_lock():
        if fcntl is None:
            yield True
            return

        lock_path = Path(settings.PRODUCTION_BACKUP_LOCK_FILE)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            try:
                yield True
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
