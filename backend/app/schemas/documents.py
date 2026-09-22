from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    page_count: int | None
    document_type: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
