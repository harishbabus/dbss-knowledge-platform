from app.models.knowledge_page import KnowledgePage
from app.services.chunk_service import ChunkService
from app.storage.knowledge_chunk_repository import (
    KnowledgeChunkRepository,
)


class IndexingService:
    def __init__(
        self,
        chunk_service: ChunkService,
        repository: KnowledgeChunkRepository,
    ):
        self.chunk_service = chunk_service

        self.repository = repository

    def index_page(
        self,
        page: KnowledgePage,
    ) -> None:
        chunks = self.chunk_service.chunk_page(page)

        self.repository.save_many(chunks)
