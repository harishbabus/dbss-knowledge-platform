from __future__ import annotations

from app.indexing.stage import IndexingStage
from app.models.indexing_context import IndexingContext
from app.models.knowledge_page import KnowledgePage


class IndexingPipeline:
    def __init__(
        self,
        stages: list[IndexingStage],
    ):
        self.stages = stages

    def process(
        self,
        page: KnowledgePage,
    ) -> IndexingContext:
        context = IndexingContext(
            page=page,
        )

        for stage in self.stages:
            context = stage.process(context)

        return context
