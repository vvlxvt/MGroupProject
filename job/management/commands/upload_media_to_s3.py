import os
import logging
from django.core.management.base import BaseCommand
import boto3
from django.conf import settings
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Upload local media folder to Yandex Object Storage"

    def handle(self, *args, **options):
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        folder = settings.MEDIA_ROOT

        logger.info(f"Starting upload from: {folder} to bucket: {bucket_name}")

        try:
            session = boto3.session.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            s3 = session.client("s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL)
        except Exception as e:
            logger.error(f"Failed to create S3 session: {e}")
            return

        for root, dirs, files in os.walk(folder):
            for file in files:
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, folder).replace("\\", "/")
                s3_key = f"{rel_path}"

                try:
                    logger.info(f"Uploading {local_path} as {s3_key}")
                    s3.upload_file(local_path, bucket_name, s3_key)
                    self.stdout.write(self.style.SUCCESS(f"Uploaded: {s3_key}"))
                except (BotoCoreError, ClientError) as e:
                    logger.error(f"Error uploading {s3_key}: {e}")

