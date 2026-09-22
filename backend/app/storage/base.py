from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta


class ObjectStorage(ABC):
    """Abstraction over a persistent object store.

    Application services depend on this interface, never on a concrete client
    (e.g. the MinIO SDK), so the storage backend can be swapped without
    touching document/extraction logic.
    """

    @abstractmethod
    def upload(self, bucket: str, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    def download(self, bucket: str, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, bucket: str, key: str) -> None: ...

    @abstractmethod
    def exists(self, bucket: str, key: str) -> bool: ...

    @abstractmethod
    def generate_presigned_url(
        self, bucket: str, key: str, expires: timedelta = timedelta(minutes=15)
    ) -> str: ...
