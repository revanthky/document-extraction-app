from __future__ import annotations

import pytest

from app.core.exceptions import InvalidPdfError
from app.pdf import service as pdf_service
from tests.conftest import make_pdf_bytes


def test_validate_pdf_accepts_valid_pdf():
    pdf_service.validate_pdf(make_pdf_bytes(num_pages=1))


def test_validate_pdf_rejects_empty_bytes():
    with pytest.raises(InvalidPdfError):
        pdf_service.validate_pdf(b"")


def test_validate_pdf_rejects_garbage_bytes():
    with pytest.raises(InvalidPdfError):
        pdf_service.validate_pdf(b"this is not a pdf file")


def test_get_page_count_single_page():
    assert pdf_service.get_page_count(make_pdf_bytes(num_pages=1)) == 1


def test_get_page_count_multi_page():
    assert pdf_service.get_page_count(make_pdf_bytes(num_pages=5)) == 5


def test_render_page_returns_png_bytes():
    data = make_pdf_bytes(num_pages=3)
    page = pdf_service.render_page(data, page_number=2, dpi=100)
    assert page.page_number == 2
    assert page.png_bytes.startswith(b"\x89PNG")


def test_render_page_out_of_range_raises():
    data = make_pdf_bytes(num_pages=2)
    with pytest.raises(InvalidPdfError):
        pdf_service.render_page(data, page_number=5)


def test_render_all_pages_preserves_order_and_count():
    data = make_pdf_bytes(num_pages=4)
    pages = pdf_service.render_all_pages(data, dpi=100)
    assert [p.page_number for p in pages] == [1, 2, 3, 4]
    assert all(p.png_bytes.startswith(b"\x89PNG") for p in pages)


def test_render_at_higher_dpi_produces_larger_image():
    data = make_pdf_bytes(num_pages=1)
    low = pdf_service.render_page(data, page_number=1, dpi=72)
    high = pdf_service.render_page(data, page_number=1, dpi=300)
    assert len(high.png_bytes) > len(low.png_bytes)
