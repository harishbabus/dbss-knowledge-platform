from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.indexing_context import IndexingContext


class IndexingStage(ABC):
    @abstractmethod
    def process(
        self,
        context: IndexingContext,
    ) -> IndexingContext:
        """
        Executes one indexing stage.
        """
        raise NotImplementedError
