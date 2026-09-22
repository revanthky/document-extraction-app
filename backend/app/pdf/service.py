from __future__ import annotations

from dataclasses import dataclass

import pymupdf as fitz

from app.core.exceptions import InvalidPdfError


@dataclass
class RenderedPage:
    page_number: int  # 1-indexed
    png_bytes: bytes


def validate_pdf(data: bytes) -> None:
    """Raise InvalidPdfError if `data` is not a well-formed, non-empty PDF."""
    if not data:
        raise InvalidPdfError("The uploaded PDF is empty.")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises various errors for corrupt files
        raise InvalidPdfError("The uploaded file is not a valid PDF.") from exc
    try:
        if doc.page_count < 1:
            raise InvalidPdfError("The uploaded PDF has no pages.")
        if doc.is_encrypted:
            raise InvalidPdfError("Encrypted/password-protected PDFs are not supported.")
    finally:
        doc.close()


def get_page_count(data: bytes) -> int:
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        return doc.page_count
    finally:
        doc.close()


def render_page(data: bytes, page_number: int, dpi: int = 150) -> RenderedPage:
    """Render a single 1-indexed page as a PNG."""
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        if page_number < 1 or page_number > doc.page_count:
            raise InvalidPdfError(f"Page {page_number} does not exist in this document.")
        page = doc.load_page(page_number - 1)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)
        return RenderedPage(page_number=page_number, png_bytes=pixmap.tobytes("png"))
    finally:
        doc.close()


def render_all_pages(data: bytes, dpi: int = 150) -> list[RenderedPage]:
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pages = []
        for index in range(doc.page_count):
            page = doc.load_page(index)
            pixmap = page.get_pixmap(matrix=matrix)
            pages.append(RenderedPage(page_number=index + 1, png_bytes=pixmap.tobytes("png")))
        return pages
    finally:
        doc.close()
