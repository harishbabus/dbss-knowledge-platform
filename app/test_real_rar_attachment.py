from __future__ import annotations

from app.bootstrap.container import Container
from app.connectors.confluence_client import ConfluenceClient
from app.crawler.inventory import KnowledgeCrawler
from app.models.attachment import Attachment
from app.models.attachment_processing_result import AttachmentProcessingStatus


PAGE_ID = "199314447"


def test_real_rar_attachment():
    """
    Real Confluence integration test for exactly one RAR attachment.

    The page is real and the attachment is downloaded/extracted through
    the real pipeline. Attachment selection is restricted to the first
    real RAR returned by Confluence so this test does not process the
    other attachments on the page.
    """

    container = Container()
    client = ConfluenceClient()

    attachments = client.get_attachments(PAGE_ID)

    rar_attachments = [
        item
        for item in attachments
        if str(item.get("filename", "")).lower().endswith(".rar")
    ]

    assert rar_attachments, f"Expected at least one RAR attachment on page {PAGE_ID}"

    target_data = {
        key: value
        for key, value in rar_attachments[0].items()
        if key in Attachment.model_fields
    }

    target_data["page_id"] = PAGE_ID

    target = Attachment(**target_data)

    attachment_id = str(target.id)

    print()
    print("=" * 70)
    print("REAL RAR ATTACHMENT TEST")
    print("=" * 70)
    print(f"Page ID       : {PAGE_ID}")
    print(f"Attachment ID : {target.id}")
    print(f"Filename      : {target.filename}")
    print("=" * 70)

    #
    # Reset only the target attachment's previous state.
    #
    container.attachment_repository.collection.delete_one({"id": attachment_id})
    container.attachment_content_repository.delete(attachment_id)

    #
    # Keep the real page processing path, but restrict PageProcessor to
    # this one attachment. We also prevent the test from treating the
    # page's other existing attachment records as deleted.
    #
    original_attachment_extract = container.page_processor.attachment_extractor.extract
    original_load_existing = container.page_processor._load_existing_attachments

    container.page_processor.attachment_extractor.extract = (
        lambda page_id, attachment_data: [target]
    )

    container.page_processor._load_existing_attachments = lambda page_id: {}

    crawler = KnowledgeCrawler(
        page_processor=container.page_processor,
    )

    original_get_pages = crawler.client.get_pages
    calls = 0

    def get_one_page(*, start: int = 0, limit: int = 100):
        nonlocal calls

        if calls == 0:
            calls += 1
            return {"results": [{"id": PAGE_ID}]}

        return {"results": []}

    crawler.client.get_pages = get_one_page

    try:
        result = crawler.run(batch_size=1)
    finally:
        crawler.client.get_pages = original_get_pages
        container.page_processor.attachment_extractor.extract = (
            original_attachment_extract
        )
        container.page_processor._load_existing_attachments = original_load_existing

    print()
    print("=" * 70)
    print("CRAWLER RESULT")
    print("=" * 70)
    print(result)
    print("=" * 70)

    assert result["processed"] == 1
    assert result["saved"] == 1
    assert result["failed"] == 0

    stored_attachment = container.attachment_repository.collection.find_one(
        {"id": attachment_id}
    )

    assert stored_attachment is not None

    print()
    print("=" * 70)
    print("RAR ATTACHMENT RESULT")
    print("=" * 70)
    print(f"ID               : {stored_attachment.get('id')}")
    print(f"Filename         : {stored_attachment.get('filename')}")
    print(f"Processing status: {stored_attachment.get('processing_status')}")
    print(f"Indexed          : {stored_attachment.get('indexed')}")
    print(f"Content hash     : {stored_attachment.get('content_hash')}")
    print(f"Processing error : {stored_attachment.get('processing_error')}")
    print("=" * 70)

    assert (
        stored_attachment.get("processing_status") == AttachmentProcessingStatus.SUCCESS
    )
    assert stored_attachment.get("indexed") is True
    assert stored_attachment.get("content_hash")

    chunks = container.attachment_content_repository.get_chunks(attachment_id)

    assert chunks

    reconstructed = "".join(chunk.get("text") or "" for chunk in chunks)

    print()
    print("=" * 70)
    print("EXTRACTED CONTENT")
    print("=" * 70)
    print(f"Chunks       : {len(chunks)}")
    print(f"Text length  : {len(reconstructed)}")
    print(f"Preview      : {reconstructed[:500]}")
    print("=" * 70)

    assert reconstructed.strip()

    assert all(chunk.get("attachment_id") == attachment_id for chunk in chunks)

    assert [chunk.get("chunk_index") for chunk in chunks] == list(range(len(chunks)))

    assert all(
        chunk.get("content_hash") == stored_attachment.get("content_hash")
        for chunk in chunks
    )
