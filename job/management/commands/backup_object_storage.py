import hashlib
import json
import logging
from datetime import UTC, datetime

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Incrementally copy media objects and upload a point-in-time manifest"

    def handle(self, *args, **options):
        source_bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "").strip()
        backup_bucket = settings.BACKUP_S3_BUCKET.strip()
        if not source_bucket:
            raise CommandError("AWS_STORAGE_BUCKET_NAME is not configured")
        if not backup_bucket:
            raise CommandError("BACKUP_S3_BUCKET is not configured")
        if source_bucket == backup_bucket:
            raise CommandError("The backup bucket must be separate from the media bucket")
        if not settings.BACKUP_S3_ACCESS_KEY_ID or not settings.BACKUP_S3_SECRET_ACCESS_KEY:
            raise CommandError("Backup Object Storage credentials are not configured")

        client = boto3.client(
            "s3",
            endpoint_url=settings.BACKUP_S3_ENDPOINT_URL,
            aws_access_key_id=settings.BACKUP_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.BACKUP_S3_SECRET_ACCESS_KEY,
        )
        created_at = datetime.now(UTC)
        root_prefix = settings.BACKUP_S3_PREFIX.strip("/")
        object_prefix = self._join(root_prefix, "object-storage", "objects")
        manifest_prefix = self._join(root_prefix, "object-storage", "manifests")

        manifest_objects = []
        copied = 0
        total_size = 0
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=source_bucket):
            for source_object in page.get("Contents", []):
                source_key = source_object["Key"]
                size = source_object["Size"]
                etag = source_object.get("ETag", "").strip('"')
                identity = hashlib.sha256(
                    f"{source_key}\0{size}\0{etag}".encode("utf-8")
                ).hexdigest()
                backup_key = self._join(object_prefix, identity[:2], identity)

                backup_object = self._head(client, backup_bucket, backup_key)
                if backup_object is None:
                    client.copy_object(
                        Bucket=backup_bucket,
                        Key=backup_key,
                        CopySource={"Bucket": source_bucket, "Key": source_key},
                        MetadataDirective="COPY",
                    )
                    copied += 1
                    backup_object = self._head(client, backup_bucket, backup_key)
                if backup_object is None or backup_object.get("ContentLength") != size:
                    raise CommandError(
                        f"Copied media object size verification failed: {source_key}"
                    )

                total_size += size
                manifest_objects.append(
                    {
                        "key": source_key,
                        "backup_key": backup_key,
                        "size": size,
                        "etag": etag,
                        "last_modified": source_object["LastModified"].isoformat(),
                    }
                )

        manifest = {
            "format": 1,
            "created_at": created_at.isoformat(),
            "source_bucket": source_bucket,
            "object_count": len(manifest_objects),
            "total_size": total_size,
            "objects": manifest_objects,
        }
        manifest_body = json.dumps(
            manifest, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        checksum = hashlib.sha256(manifest_body).hexdigest()
        manifest_key = self._join(
            manifest_prefix,
            created_at.strftime("%Y/%m/%d"),
            f"manifest-{created_at.strftime('%Y%m%dT%H%M%SZ')}.json",
        )
        client.put_object(
            Bucket=backup_bucket,
            Key=manifest_key,
            Body=manifest_body,
            ContentType="application/json",
            Metadata={"sha256": checksum},
        )
        uploaded = client.head_object(Bucket=backup_bucket, Key=manifest_key)
        if uploaded.get("ContentLength") != len(manifest_body):
            raise CommandError("Uploaded Object Storage manifest size verification failed")
        uploaded_checksum = uploaded.get("Metadata", {}).get("sha256")
        if uploaded_checksum and uploaded_checksum != checksum:
            raise CommandError("Uploaded Object Storage manifest checksum verification failed")
        if not uploaded_checksum:
            logger.warning(
                "Backup storage did not return manifest checksum metadata; "
                "upload was verified by size"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Object Storage backup completed: "
                f"objects={len(manifest_objects)}, copied={copied}, "
                f"manifest=s3://{backup_bucket}/{manifest_key}"
            )
        )

    @staticmethod
    def _head(client, bucket, key):
        try:
            return client.head_object(Bucket=bucket, Key=key)
        except ClientError as error:
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            code = error.response.get("Error", {}).get("Code")
            if status == 404 or code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise

    @staticmethod
    def _join(*parts):
        return "/".join(part.strip("/") for part in parts if part.strip("/"))
