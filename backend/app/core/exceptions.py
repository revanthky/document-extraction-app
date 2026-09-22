from __future__ import annotations


class AppError(Exception):
    """Base class for domain errors that map to friendly API responses."""

    status_code = 400

    def __init__(self, message: str, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class InvalidPdfError(AppError):
    status_code = 422


class FileTooLargeError(AppError):
    status_code = 413


class UnsupportedFileTypeError(AppError):
    status_code = 415


class DocumentNotFoundError(AppError):
    status_code = 404


class ExtractionNotFoundError(AppError):
    status_code = 404


class ModelNotConfiguredError(AppError):
    status_code = 400


class ModelAuthError(AppError):
    status_code = 401


class ModelRateLimitError(AppError):
    status_code = 429


class ModelTimeoutError(AppError):
    status_code = 504


class ModelResponseError(AppError):
    """Raised when the Vision Model returns malformed or unparseable output."""

    status_code = 502


class StorageError(AppError):
    status_code = 502
