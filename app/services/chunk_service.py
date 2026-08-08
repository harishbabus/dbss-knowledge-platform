from __future__ import annotations


from app.chunking.base_splitter import BaseSplitter
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_page import KnowledgePage


class ChunkService:
    def __init__(
        self,
        splitter: BaseSplitter,
    ):
        self.splitter = splitter

    def chunk_page(
        self,
        page: KnowledgePage,
    ) -> list[KnowledgeChunk]:
        chunks = self.splitter.split(page)

        return [
            self._create_chunk(
                page,
                sequence,
                text,
            )
            for sequence, text in enumerate(
                chunks,
                start=1,
            )
        ]

    def _create_chunk(
        self,
        page: KnowledgePage,
        sequence: int,
        text: str,
    ) -> KnowledgeChunk:
        return KnowledgeChunk(
            id=f"{page.id}_{sequence:04d}",
            page_id=page.id,
            sequence=sequence,
            title=page.metadata.title,
            text=text,
            splitter=self.splitter.name,
            metadata={
                "space": page.metadata.space,
                "labels": page.metadata.labels,
            },
            token_count=0,
        )
