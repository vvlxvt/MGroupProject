import hashlib
import logging
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create, verify, and upload a PostgreSQL backup to private S3 storage"

    def handle(self, *args, **options):
        database = settings.DATABASES["default"]
        if database.get("ENGINE") != "django.db.backends.postgresql":
            raise CommandError("The default database is not PostgreSQL")

        bucket = settings.BACKUP_S3_BUCKET.strip()
        if not bucket:
            raise CommandError("BACKUP_S3_BUCKET is not configured")
        if bucket == getattr(settings, "AWS_STORAGE_BUCKET_NAME", None):
            raise CommandError("The backup bucket must be separate from the media bucket")
        if not settings.BACKUP_S3_ACCESS_KEY_ID or not settings.BACKUP_S3_SECRET_ACCESS_KEY:
            raise CommandError("Backup Object Storage credentials are not configured")

        created_at = datetime.now(UTC)
        prefix = settings.BACKUP_S3_PREFIX.strip("/")
        object_key = "/".join(
            part
            for part in (
                prefix,
                "postgresql",
                created_at.strftime("%Y/%m/%d"),
                f"database-{created_at.strftime('%Y%m%dT%H%M%SZ')}.dump",
            )
            if part
        )

        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".dump", delete=False) as temporary:
                temporary_path = Path(temporary.name)

            self._create_dump(database, temporary_path)
            self._verify_dump(temporary_path)
            size = temporary_path.stat().st_size
            if size <= 0:
                raise CommandError("pg_dump created an empty backup")
            checksum = self._sha256(temporary_path)

            client = boto3.client(
                "s3",
                endpoint_url=settings.BACKUP_S3_ENDPOINT_URL,
                aws_access_key_id=settings.BACKUP_S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.BACKUP_S3_SECRET_ACCESS_KEY,
            )
            client.upload_file(
                str(temporary_path),
                bucket,
                object_key,
                ExtraArgs={
                    "ContentType": "application/octet-stream",
                    "Metadata": {"sha256": checksum},
                },
            )
            uploaded = client.head_object(Bucket=bucket, Key=object_key)
            if uploaded.get("ContentLength") != size:
                raise CommandError("Uploaded backup size verification failed")
            uploaded_checksum = uploaded.get("Metadata", {}).get("sha256")
            if uploaded_checksum and uploaded_checksum != checksum:
                raise CommandError("Uploaded backup checksum verification failed")
            if not uploaded_checksum:
                logger.warning(
                    "Backup storage did not return checksum metadata; "
                    "upload was verified by size"
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"PostgreSQL backup uploaded: s3://{bucket}/{object_key} ({size} bytes)"
                )
            )
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def _create_dump(self, database, output_path):
        command = [
            "pg_dump",
            "--format=custom",
            "--compress=9",
            "--no-owner",
            "--no-acl",
            "--no-password",
            f"--file={output_path}",
            f"--host={database['HOST']}",
            f"--port={database.get('PORT') or '5432'}",
            f"--username={database['USER']}",
            database["NAME"],
        ]
        environment = os.environ.copy()
        environment["PGPASSWORD"] = str(database["PASSWORD"])
        environment["PGSSLMODE"] = settings.BACKUP_PGSSLMODE
        self._run(command, environment)

    def _verify_dump(self, output_path):
        self._run(["pg_restore", "--list", str(output_path)], os.environ.copy())

    def _run(self, command, environment):
        try:
            subprocess.run(
                command,
                env=environment,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=settings.BACKUP_DATABASE_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as error:
            raise CommandError(f"Required executable is missing: {command[0]}") from error
        except subprocess.TimeoutExpired as error:
            raise CommandError(f"Backup command timed out: {command[0]}") from error
        except subprocess.CalledProcessError as error:
            raise CommandError(
                f"Backup command failed: {command[0]} (exit code {error.returncode})"
            ) from error

    @staticmethod
    def _sha256(path):
        digest = hashlib.sha256()
        with path.open("rb") as backup_file:
            for chunk in iter(lambda: backup_file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
