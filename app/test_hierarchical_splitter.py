from app.chunking.hierarchical_splitter import (
    HierarchicalSplitter,
)
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


def test_small_sections_remain_intact():
    page = _create_page(
        """
        <h1>Overview</h1>
        <p>This is the overview.</p>

        <h2>Configuration</h2>
        <p>Configuration details.</p>

        <h2>Troubleshooting</h2>
        <p>Troubleshooting details.</p>
        """
    )

    splitter = HierarchicalSplitter(
        chunk_size=1200,
        overlap=200,
    )

    chunks = splitter.split(page)

    assert len(chunks) == 3

    assert chunks[0] == ("Overview\nThis is the overview.")

    assert chunks[1] == ("Configuration\nConfiguration details.")

    assert chunks[2] == ("Troubleshooting\nTroubleshooting details.")


def test_large_section_is_character_split():
    large_content = "A" * 2500

    page = _create_page(
        f"""
        <h2>API Reference</h2>
        <p>{large_content}</p>
        """
    )

    splitter = HierarchicalSplitter(
        chunk_size=1200,
        overlap=200,
    )

    chunks = splitter.split(page)

    assert len(chunks) > 1

    assert all(len(chunk) <= 1200 for chunk in chunks)


def test_empty_content_returns_no_chunks():
    page = _create_page("")

    splitter = HierarchicalSplitter()

    assert splitter.split(page) == []


def test_name():
    splitter = HierarchicalSplitter()

    assert splitter.name == "hierarchical"


def test_large_section_preserves_heading():
    large_content = "A" * 2500

    page = _create_page(
        f"""
        <h2>API Reference</h2>
        <p>{large_content}</p>
        """
    )

    splitter = HierarchicalSplitter(
        chunk_size=1200,
        overlap=200,
    )

    chunks = splitter.split(page)

    assert len(chunks) > 1

    assert all(len(chunk) <= 1200 for chunk in chunks)

    assert all(chunk.startswith("API Reference\n") for chunk in chunks)


def test_large_section_without_heading():
    large_content = "B" * 2500

    page = _create_page(
        f"""
        <p>{large_content}</p>
        """
    )

    splitter = HierarchicalSplitter(
        chunk_size=1200,
        overlap=200,
    )

    chunks = splitter.split(page)

    assert len(chunks) > 1

    assert all(len(chunk) <= 1200 for chunk in chunks)


def test_invalid_chunk_size():
    try:
        HierarchicalSplitter(chunk_size=0)
    except ValueError as exc:
        assert "chunk_size" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_invalid_overlap():
    try:
        HierarchicalSplitter(
            chunk_size=100,
            overlap=100,
        )
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_nested_div_content_is_preserved():
    page = _create_page(
        """
        <div>
            <h2>Configuration</h2>
            <div>
                <p>Database configuration.</p>
                <div>
                    <p>Connection details.</p>
                </div>
            </div>
        </div>
        """
    )

    splitter = HierarchicalSplitter()

    chunks = splitter.split(page)

    assert len(chunks) == 1

    assert chunks[0].startswith("Configuration\n")

    assert "Database configuration." in chunks[0]
    assert "Connection details." in chunks[0]


def test_list_content_is_preserved():
    page = _create_page(
        """
        <h2>Configuration</h2>
        <ul>
            <li>Property A</li>
            <li>Property B</li>
            <li>Property C</li>
        </ul>
        """
    )

    splitter = HierarchicalSplitter()

    chunks = splitter.split(page)

    assert len(chunks) == 1

    assert "Property A" in chunks[0]
    assert "Property B" in chunks[0]
    assert "Property C" in chunks[0]


def test_table_content_is_preserved():
    page = _create_page(
        """
        <h2>Configuration</h2>

        <table>
            <tr>
                <th>Property</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>host</td>
                <td>localhost</td>
            </tr>
            <tr>
                <td>port</td>
                <td>8080</td>
            </tr>
        </table>
        """
    )

    splitter = HierarchicalSplitter()

    chunks = splitter.split(page)

    assert len(chunks) == 1

    assert "Property" in chunks[0]
    assert "Value" in chunks[0]
    assert "host" in chunks[0]
    assert "localhost" in chunks[0]
    assert "8080" in chunks[0]


def test_code_block_content_is_preserved():
    page = _create_page(
        """
        <h2>API Example</h2>

        <pre>
        curl -X GET https://example.com/customer/123
        </pre>
        """
    )

    splitter = HierarchicalSplitter()

    chunks = splitter.split(page)

    assert len(chunks) == 1

    assert "curl -X GET" in chunks[0]
    assert "/customer/123" in chunks[0]


def test_content_before_first_heading_is_preserved():
    page = _create_page(
        """
        <p>Introduction content.</p>

        <h2>Configuration</h2>
        <p>Configuration details.</p>
        """
    )

    splitter = HierarchicalSplitter()

    chunks = splitter.split(page)

    assert len(chunks) == 2

    assert chunks[0] == ("Introduction content.")

    assert chunks[1] == ("Configuration\nConfiguration details.")


def test_consecutive_headings_are_preserved():
    page = _create_page(
        """
        <h1>API</h1>

        <h2>REST</h2>
        <p>REST API details.</p>

        <h2>SOAP</h2>
        <p>SOAP API details.</p>
        """
    )

    splitter = HierarchicalSplitter()

    chunks = splitter.split(page)

    assert len(chunks) == 3

    assert chunks[0] == "API"

    assert chunks[1] == ("REST\nREST API details.")

    assert chunks[2] == ("SOAP\nSOAP API details.")


def test_heading_without_content_is_preserved():
    page = _create_page(
        """
        <h1>Overview</h1>

        <h2>Configuration</h2>

        <h2>Troubleshooting</h2>
        <p>Troubleshooting details.</p>
        """
    )

    splitter = HierarchicalSplitter()

    chunks = splitter.split(page)

    assert len(chunks) == 3

    assert chunks[0] == "Overview"

    assert chunks[1] == "Configuration"

    assert chunks[2] == ("Troubleshooting\nTroubleshooting details.")


def test_standalone_heading_is_preserved():
    page = _create_page(
        """
        <h2>Configuration</h2>
        """
    )

    splitter = HierarchicalSplitter()

    chunks = splitter.split(page)

    assert chunks == ["Configuration"]
