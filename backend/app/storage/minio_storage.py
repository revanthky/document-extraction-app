from __future__ import annotations

import io
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.exceptions import StorageError
from app.core.logging import get_logger
from app.storage.base import ObjectStorage

logger = get_logger(__name__)


class MinIOObjectStorage(ObjectStorage):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ):
        self._client = Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=secure
        )

    def ensure_bucket(self, bucket: str) -> None:
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
        except S3Error as exc:
            raise StorageError("Failed to prepare object storage bucket") from exc

    def upload(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        try:
            self.ensure_bucket(bucket)
            self._client.put_object(
                bucket, key, io.BytesIO(data), length=len(data), content_type=content_type
            )
        except S3Error as exc:
            logger.error("minio_upload_failed", extra={"bucket": bucket, "key": key})
            raise StorageError("Failed to upload document to object storage") from exc

    def download(self, bucket: str, key: str) -> bytes:
        response = None
        try:
            response = self._client.get_object(bucket, key)
            return response.read()
        except S3Error as exc:
            raise StorageError("Failed to download document from object storage") from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def delete(self, bucket: str, key: str) -> None:
        try:
            self._client.remove_object(bucket, key)
        except S3Error as exc:
            raise StorageError("Failed to delete document from object storage") from exc

    def exists(self, bucket: str, key: str) -> bool:
        try:
            self._client.stat_object(bucket, key)
            return True
        except S3Error as exc:
            if exc.code in ("NoSuchKey", "NoSuchBucket"):
                return False
            raise StorageError("Failed to check object existence") from exc

    def generate_presigned_url(
        self, bucket: str, key: str, expires: timedelta = timedelta(minutes=15)
    ) -> str:
        try:
            return self._client.presigned_get_object(bucket, key, expires=expires)
        except S3Error as exc:
            raise StorageError("Failed to generate presigned URL") from exc


def split_endpoint(endpoint: str, default_secure: bool) -> tuple[str, bool]:
    """Strip a scheme from a MinIO endpoint, if present, and resolve `secure` from it.

    DKubeX's auto-provisioned `minio` dependency injects a scheme-qualified endpoint
    (e.g. `http://minio.dkubex.svc:9000`; see package-app skill, references/dependencies.md),
    but the minio-py client's `endpoint` argument must be bare `host:port` -- the scheme is
    conveyed separately via `secure`. Local dev already configures a bare endpoint.
    """
    if endpoint.startswith("https://"):
        return endpoint[len("https://") :], True
    if endpoint.startswith("http://"):
        return endpoint[len("http://") :], False
    return endpoint, default_secure


_storage: MinIOObjectStorage | None = None


def get_object_storage() -> MinIOObjectStorage:
    global _storage
    if _storage is None:
        from app.config import get_app_config

        cfg = get_app_config()
        endpoint, secure = split_endpoint(cfg.minio_endpoint, cfg.minio_secure)
        _storage = MinIOObjectStorage(
            endpoint=endpoint,
            access_key=cfg.minio_access_key,
            secret_key=cfg.minio_secret_key,
            secure=secure,
        )
    return _storage
