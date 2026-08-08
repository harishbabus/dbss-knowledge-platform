from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.knowledge_page import KnowledgePage


class BaseSplitter(ABC):
    """
    Base interface for all chunking strategies.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def split(
        self,
        page: KnowledgePage,
    ) -> list[str]:
        """
        Splits a KnowledgePage into text chunks.
        """
        raise NotImplementedError
