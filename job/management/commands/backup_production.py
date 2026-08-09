from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Back up PostgreSQL and Object Storage"

    def handle(self, *args, **options):
        call_command("backup_postgres")
        call_command("backup_object_storage")
