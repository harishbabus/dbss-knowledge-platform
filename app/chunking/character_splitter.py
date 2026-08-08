from __future__ import annotations

from app.chunking.base_splitter import BaseSplitter
from app.models.knowledge_page import KnowledgePage


class CharacterSplitter(BaseSplitter):
    def __init__(
        self,
        chunk_size: int = 1200,
        overlap: int = 200,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if overlap < 0:
            raise ValueError("overlap cannot be negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    @property
    def name(self) -> str:
        return "character"

    def split(
        self,
        page: KnowledgePage,
    ) -> list[str]:
        text = page.content.get(
            "plain_text",
            "",
        )

        if not text.strip():
            return []

        chunks: list[str] = []

        start = 0

        while start < len(text):
            end = min(
                start + self.chunk_size,
                len(text),
            )

            chunks.append(text[start:end])

            if end == len(text):
                break

            start = end - self.overlap

        return chunks
