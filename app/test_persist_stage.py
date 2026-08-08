from app.indexing.persist_stage import PersistStage
from app.models.indexing_context import IndexingContext
from app.models.knowledge_page import KnowledgePage
from app.models.page_metadata import PageMetadata
from app.models.sync_metadata import SyncMetadata


class FakeKnowledgeChunkRepository:
    def __init__(self):
        self.calls = []

    def replace_for_page(self, page_id, chunks):
        self.calls.append(
            {
                "page_id": page_id,
                "chunks": chunks,
            }
        )


def _create_page() -> KnowledgePage:
    return KnowledgePage(
        id="test-page",
        metadata=PageMetadata(
            title="Test Page",
            space="DPCC",
            status="current",
            version=1,
            created_by=None,
            created_date=None,
            updated_by=None,
            updated_date=None,
            parent_id=None,
            url="",
        ),
        content={
            "raw_html": "",
            "plain_text": "",
            "headings": [],
            "tables": [],
            "code_blocks": [],
            "links": [],
            "macros": [],
            "content_hash": "test",
        },
        attachments=[],
        sync=SyncMetadata(
            content_hash="test",
            last_synced="2026-01-01T00:00:00+00:00",
            source="Confluence",
        ),
    )


def test_persist_stage_replaces_chunks_for_page():
    repository = FakeKnowledgeChunkRepository()

    stage = PersistStage(repository)

    context = IndexingContext(
        page=_create_page(),
        chunks=[],
    )

    result = stage.process(context)

    assert len(repository.calls) == 1

    assert repository.calls[0]["page_id"] == "test-page"

    assert repository.calls[0]["chunks"] == []

    assert "PersistStage" in result.completed_stages


def test_persist_stage_passes_current_chunks():
    repository = FakeKnowledgeChunkRepository()

    stage = PersistStage(repository)

    context = IndexingContext(
        page=_create_page(),
        chunks=[],
    )

    result = stage.process(context)

    assert result is context

    assert repository.calls[0]["page_id"] == "test-page"
    assert repository.calls[0]["chunks"] == context.chunks
