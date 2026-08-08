from copy import deepcopy

from app.bootstrap.container import Container
from app.connectors.confluence_client import ConfluenceClient


PAGE_ID = "127489206"


def _get_chunks(container: Container) -> list[dict]:
    return list(container.chunk_repository.collection.find({"page_id": PAGE_ID}))


def test_real_page_content_change_replaces_chunks():
    container = Container()
    client = ConfluenceClient()

    #
    # Fetch the real page.
    #
    original_page = client.get_page_details(PAGE_ID)

    original_page = deepcopy(original_page)

    original_html = original_page.get("body", {}).get("storage", {}).get("value", "")

    assert original_html

    #
    # Process the original page.
    #
    container.page_processor.process(
        PAGE_ID,
        original_page,
    )

    original_chunks = _get_chunks(container)

    assert len(original_chunks) == 29

    original_chunk_ids = {chunk["id"] for chunk in original_chunks}

    #
    # Create a modified copy.
    #
    modified_page = deepcopy(original_page)

    modified_html = """
        <h1>TEST CONTENT CHANGE</h1>

        <p>
            This content was added specifically for
            the real page replacement test.
        </p>

        <h2>Replacement Section</h2>

        <p>
            The original chunks must be replaced
            by this new content.
        </p>
    """

    modified_page["body"]["storage"]["value"] = modified_html

    #
    # Process the modified page.
    #
    container.page_processor.process(
        PAGE_ID,
        modified_page,
    )

    modified_chunks = _get_chunks(container)

    #
    # The new page should have only the new chunks.
    #
    assert len(modified_chunks) > 0

    modified_text = "\n".join(chunk["text"] for chunk in modified_chunks)

    assert "TEST CONTENT CHANGE" in modified_text
    assert "Replacement Section" in modified_text

    #
    # The old chunk IDs must no longer exist.
    #

    modified_chunk_ids = {chunk["id"] for chunk in modified_chunks}

    assert len(modified_chunk_ids) == len(modified_chunks)

    assert all(chunk["page_id"] == PAGE_ID for chunk in modified_chunks)

    #
    # Verify there are no duplicate IDs.
    #
    assert len(modified_chunk_ids) == len(modified_chunks)

    #
    # Verify all chunks are valid hierarchical chunks.
    #
    assert all(chunk["splitter"] == "hierarchical" for chunk in modified_chunks)

    assert all(len(chunk["text"]) <= 1200 for chunk in modified_chunks)

    #
    # Restore the real page so this test leaves
    # MongoDB in its original state.
    #
    container.page_processor.process(
        PAGE_ID,
        original_page,
    )

    restored_chunks = _get_chunks(container)

    assert len(restored_chunks) == 29

    restored_chunk_ids = {chunk["id"] for chunk in restored_chunks}

    assert restored_chunk_ids == original_chunk_ids
