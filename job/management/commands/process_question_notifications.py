from django.core.management.base import BaseCommand
from django.db import transaction

from job.models import UserQuestion
from job.utils import send_telegram_message


class Command(BaseCommand):
    help = "Send queued question notifications to Telegram"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--retry-failed", action="store_true")

    def handle(self, *args, **options):
        statuses = [UserQuestion.DeliveryStatus.PENDING]
        if options["retry_failed"]:
            statuses.append(UserQuestion.DeliveryStatus.FAILED)

        attempted_ids = []
        sent_count = 0
        failed_count = 0

        while len(attempted_ids) < options["limit"]:
            with transaction.atomic():
                question = (
                    UserQuestion.objects.select_for_update(skip_locked=True)
                    .select_related("user")
                    .filter(telegram_status__in=statuses)
                    .exclude(pk__in=attempted_ids)
                    .order_by("created_at")
                    .first()
                )
                if question is None:
                    break

                attempted_ids.append(question.pk)
                telegram_sent = send_telegram_message(question)
                question.telegram_status = (
                    UserQuestion.DeliveryStatus.SENT
                    if telegram_sent
                    else UserQuestion.DeliveryStatus.FAILED
                )
                question.save(update_fields=["telegram_status"])

                if telegram_sent:
                    sent_count += 1
                else:
                    failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(attempted_ids)} question(s): "
                f"sent={sent_count}, failed={failed_count}"
            )
        )
