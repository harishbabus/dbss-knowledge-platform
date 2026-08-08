from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    """
    Represents a semantically searchable chunk
    extracted from a KnowledgePage.
    """

    id: str

    page_id: str

    sequence: int

    title: str

    text: str

    splitter: str

    metadata: dict[str, Any] = Field(default_factory=dict)

    token_count: int = 0

    embedding_model: str | None = None

    embedding_version: int = 1

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
