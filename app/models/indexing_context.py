from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_page import KnowledgePage


class IndexingContext(BaseModel):
    """
    Shared state that flows through the indexing pipeline.
    """

    page: KnowledgePage

    chunks: list[KnowledgeChunk] = Field(default_factory=list)

    embeddings: list[list[float]] = Field(default_factory=list)

    metadata: dict = Field(default_factory=dict)

    completed_stages: list[str] = Field(default_factory=list)
