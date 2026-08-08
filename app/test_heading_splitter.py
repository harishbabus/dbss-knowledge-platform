from app.chunking.heading_splitter import HeadingSplitter
from app.models.knowledge_page import KnowledgePage
from app.models.page_metadata import PageMetadata
from app.models.sync_metadata import SyncMetadata


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


def test_heading_splitter():
    html = """
    <h1>Overview</h1>
    <p>This is the overview.</p>

    <h2>Configuration</h2>
    <p>These are configuration details.</p>

    <h2>Troubleshooting</h2>
    <p>These are troubleshooting details.</p>
    """

    splitter = HeadingSplitter()

    page = _create_page(html)

    chunks = splitter.split(page)

    assert len(chunks) == 3

    assert chunks[0] == ("Overview\nThis is the overview.")

    assert chunks[1] == ("Configuration\nThese are configuration details.")

    assert chunks[2] == ("Troubleshooting\nThese are troubleshooting details.")


def test_heading_splitter_without_headings():
    html = """
    <p>This is some content.</p>
    <p>More content follows.</p>
    """

    splitter = HeadingSplitter()

    page = _create_page(html)

    chunks = splitter.split(page)

    assert len(chunks) == 1

    assert chunks[0] == ("This is some content.\nMore content follows.")


def test_heading_splitter_empty_content():
    page = _create_page("")

    splitter = HeadingSplitter()

    chunks = splitter.split(page)

    assert chunks == []


def test_heading_splitter_name():
    splitter = HeadingSplitter()

    assert splitter.name == "heading"
