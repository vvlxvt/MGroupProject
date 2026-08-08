import logging
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import close_old_connections


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Continuously process queued feedback notifications"

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=60)
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        interval = max(options["interval"], 10)
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

            if options["once"]:
                return
            first_iteration = False
            time.sleep(interval)
