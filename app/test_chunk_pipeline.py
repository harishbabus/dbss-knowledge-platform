from app.chunking.heading_splitter import HeadingSplitter
from app.indexing.chunk_stage import ChunkStage
from app.indexing.pipeline import IndexingPipeline
from app.models.knowledge_page import KnowledgePage
from app.models.page_metadata import PageMetadata
from app.models.sync_metadata import SyncMetadata
from app.services.chunk_service import ChunkService


def _create_page(html: str) -> KnowledgePage:
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
            "raw_html": html,
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


def test_heading_splitter_through_pipeline():
    page = _create_page(
        """
        <h1>Overview</h1>
        <p>This is the overview.</p>

        <h2>Configuration</h2>
        <p>These are configuration details.</p>

        <h2>Troubleshooting</h2>
        <p>These are troubleshooting details.</p>
        """
    )

    chunk_service = ChunkService(HeadingSplitter())

    pipeline = IndexingPipeline(
        [
            ChunkStage(chunk_service),
        ]
    )

    result = pipeline.process(page)

    assert len(result.chunks) == 3

    assert result.chunks[0].splitter == "heading"
    assert result.chunks[1].splitter == "heading"
    assert result.chunks[2].splitter == "heading"

    assert result.chunks[0].sequence == 1
    assert result.chunks[1].sequence == 2
    assert result.chunks[2].sequence == 3

    assert result.chunks[0].id == "test-page_0001"
    assert result.chunks[1].id == "test-page_0002"
    assert result.chunks[2].id == "test-page_0003"

    assert "ChunkStage" in result.completed_stages
