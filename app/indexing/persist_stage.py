from __future__ import annotations

from app.indexing.stage import IndexingStage
from app.models.indexing_context import IndexingContext
from app.storage.knowledge_chunk_repository import (
    KnowledgeChunkRepository,
)


class PersistStage(IndexingStage):
    def __init__(
        self,
        repository: KnowledgeChunkRepository,
    ):
        self.repository = repository

    def process(
        self,
        context: IndexingContext,
    ) -> IndexingContext:
        self.repository.replace_for_page(
            context.page.id,
            context.chunks,
        )

        context.completed_stages.append("PersistStage")

        return context
