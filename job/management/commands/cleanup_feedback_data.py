from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from job.models import ApplicantProfile, UserProfile, UserQuestion


class Command(BaseCommand):
    help = "Delete expired feedback records and their uploaded files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=settings.FEEDBACK_RETENTION_DAYS,
            help="Retention period in days",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Apply deletion; without this flag the command is a dry run",
        )
        parser.add_argument(
            "--purge-legacy-profiles",
            action="store_true",
            help="Also delete obsolete Telegram profiles and profile photos",
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            raise CommandError("Retention period must be at least one day")

        cutoff = timezone.now() - timedelta(days=days)
        questions = UserQuestion.objects.filter(created_at__lt=cutoff).exclude(
            telegram_status=UserQuestion.DeliveryStatus.PENDING
        )
        question_count = questions.count()
        applicants = ApplicantProfile.objects.filter(created_at__lt=cutoff).exclude(
            telegram_status=UserQuestion.DeliveryStatus.PENDING
        )
        applicant_count = applicants.count()
        profile_count = (
            UserProfile.objects.count() if options["purge_legacy_profiles"] else 0
        )

        if not options["delete"]:
            self.stdout.write(
                f"Dry run: questions={question_count}, applicants={applicant_count}, "
                f"legacy_profiles={profile_count}, "
                f"cutoff={cutoff.isoformat()}"
            )
            return

        for question in questions.iterator():
            if question.attached_photo:
                question.attached_photo.delete(save=False)
        questions.delete()
        applicants.delete()

        if options["purge_legacy_profiles"]:
            for profile in UserProfile.objects.all().iterator():
                if profile.photo:
                    profile.photo.delete(save=False)
            UserProfile.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted questions={question_count}, applicants={applicant_count}, "
                f"legacy_profiles={profile_count}"
            )
        )
