from __future__ import annotations

from app.indexing.stage import IndexingStage
from app.models.indexing_context import IndexingContext
from app.services.chunk_service import ChunkService


class ChunkStage(IndexingStage):
    def __init__(
        self,
        chunk_service: ChunkService,
    ):
        self.chunk_service = chunk_service

    def process(
        self,
        context: IndexingContext,
    ) -> IndexingContext:
        context.chunks = self.chunk_service.chunk_page(context.page)

        context.completed_stages.append("ChunkStage")

        return context
