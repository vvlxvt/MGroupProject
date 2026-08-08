from django.core.management.base import BaseCommand

from job.models import ApplicantProfile, UserQuestion
from job.utils import send_telegram_applicant, send_telegram_message


class Command(BaseCommand):
    help = "Send queued questions and vacancy responses to the owner's Telegram chat"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--retry-failed", action="store_true")

    def handle(self, *args, **options):
        statuses = [UserQuestion.DeliveryStatus.PENDING]
        if options["retry_failed"]:
            statuses.append(UserQuestion.DeliveryStatus.FAILED)

        remaining = max(options["limit"], 0)
        sent = failed = 0
        sources = (
            (UserQuestion, send_telegram_message),
            (ApplicantProfile, send_telegram_applicant),
        )
        for model, sender in sources:
            records = model.objects.filter(telegram_status__in=statuses).order_by(
                "created_at"
            )[:remaining]
            for record in records:
                delivered = sender(record)
                record.telegram_status = (
                    UserQuestion.DeliveryStatus.SENT
                    if delivered
                    else UserQuestion.DeliveryStatus.FAILED
                )
                record.save(update_fields=["telegram_status"])
                sent += int(delivered)
                failed += int(not delivered)
                remaining -= 1
            if remaining == 0:
                break

        self.stdout.write(
            self.style.SUCCESS(f"Processed feedback: sent={sent}, failed={failed}")
        )
