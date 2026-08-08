from app.chunking.hierarchical_splitter import HierarchicalSplitter
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


def test_hierarchical_splitter_through_pipeline():
    page = _create_page(
        """
        <h1>Overview</h1>
        <p>This is the overview.</p>

        <h2>Configuration</h2>
        <p>These are configuration details.</p>

        <h2>API Reference</h2>
        <p>
            This is a large API reference section.
        </p>
        """
    )

    chunk_service = ChunkService(
        HierarchicalSplitter(
            chunk_size=1200,
            overlap=200,
        )
    )

    pipeline = IndexingPipeline(
        [
            ChunkStage(chunk_service),
        ]
    )

    result = pipeline.process(page)

    assert len(result.chunks) == 3

    assert result.chunks[0].splitter == "hierarchical"
    assert result.chunks[1].splitter == "hierarchical"
    assert result.chunks[2].splitter == "hierarchical"

    assert result.chunks[0].sequence == 1
    assert result.chunks[1].sequence == 2
    assert result.chunks[2].sequence == 3

    assert result.chunks[0].id == "test-page_0001"
    assert result.chunks[1].id == "test-page_0002"
    assert result.chunks[2].id == "test-page_0003"

    assert result.chunks[0].text == ("Overview\nThis is the overview.")

    assert result.chunks[1].text == ("Configuration\nThese are configuration details.")

    assert result.chunks[2].text == (
        "API Reference\nThis is a large API reference section."
    )

    assert "ChunkStage" in result.completed_stages


def test_large_section_preserves_heading_through_pipeline():
    large_content = "A" * 2500

    page = _create_page(
        f"""
        <h1>Overview</h1>
        <p>This is the overview.</p>

        <h2>API Reference</h2>
        <p>{large_content}</p>
        """
    )

    chunk_service = ChunkService(
        HierarchicalSplitter(
            chunk_size=1200,
            overlap=200,
        )
    )

    pipeline = IndexingPipeline(
        [
            ChunkStage(chunk_service),
        ]
    )

    result = pipeline.process(page)

    assert len(result.chunks) == 4

    #
    # Overview
    #
    assert result.chunks[0].text == ("Overview\nThis is the overview.")

    #
    # API Reference chunks
    #
    api_chunks = result.chunks[1:]

    assert len(api_chunks) == 3

    assert all(chunk.splitter == "hierarchical" for chunk in api_chunks)

    assert all(chunk.text.startswith("API Reference\n") for chunk in api_chunks)

    assert all(len(chunk.text) <= 1200 for chunk in api_chunks)

    assert [chunk.sequence for chunk in result.chunks] == [
        1,
        2,
        3,
        4,
    ]

    assert "ChunkStage" in result.completed_stages
