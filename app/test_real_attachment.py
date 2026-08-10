from __future__ import annotations

from app.bootstrap.container import Container
from app.connectors.confluence_client import ConfluenceClient
from app.crawler.inventory import KnowledgeCrawler
from app.models.attachment_processing_result import AttachmentProcessingStatus


PAGE_ID = "199314447"


def _root_attachment_id(content_id: str) -> str:
    """
    Convert an attachment-content document ID back to its
    root attachment ID.

    Examples:
        199321138
        199321138__chunk_000001
        199321138__chunk_000002

    all belong to attachment 199321138.
    """
    return content_id.split("__chunk_", 1)[0]


def test_real_attachment_single_file_page():
    """
    Real Confluence attachment integration test for page 199314447.

    The page contains a large number of attachments.

    The test validates:

    - real attachment discovery from Confluence
    - real attachment processing through KnowledgeCrawler
    - attachment metadata persistence
    - extracted-content persistence
    - SHA-256 content hash persistence
    - successful attachments have persisted content
    - large extracted content may be stored as multiple chunks
    - failed attachments are reported with their exact status

    Important:
        One attachment may produce multiple attachment_contents
        documents because large extracted content is chunked.

        Therefore this test validates attachment-level content
        coverage rather than comparing the number of MongoDB
        content documents with the number of attachments.
    """

    container = Container()
    client = ConfluenceClient()

    #
    # Discover the real attachments first.
    #
    attachments = client.get_attachments(PAGE_ID)

    assert attachments, f"Expected attachments on page {PAGE_ID}"

    attachment_ids = {
        str(item["id"]) for item in attachments if item.get("id") is not None
    }

    assert attachment_ids

    #
    # Reset only this page's attachment state so this run exercises
    # the real download/extraction path.
    #
    container.attachment_repository.collection.delete_many(
        {"id": {"$in": list(attachment_ids)}}
    )

    container.attachment_content_repository.collection.delete_many(
        {
            "page_id": PAGE_ID,
        }
    )

    #
    # Use the real crawler logic but restrict pagination to this page.
    #
    crawler = KnowledgeCrawler(page_processor=container.page_processor)

    original_get_pages = crawler.client.get_pages

    calls = 0

    def get_one_page(*, start: int = 0, limit: int = 100):
        nonlocal calls

        if calls == 0:
            calls += 1

            return {
                "results": [
                    {
                        "id": PAGE_ID,
                    }
                ]
            }

        return {"results": []}

    crawler.client.get_pages = get_one_page

    try:
        result = crawler.run(batch_size=1)
    finally:
        crawler.client.get_pages = original_get_pages

    #
    # Exactly one real Confluence page was processed.
    #
    assert result == {
        "processed": 1,
        "saved": 1,
        "failed": 0,
    }

    #
    # Read the attachment metadata persisted by the real pipeline.
    #
    stored_attachments = list(
        container.attachment_repository.collection.find(
            {"id": {"$in": list(attachment_ids)}}
        )
    )

    assert len(stored_attachments) == len(attachment_ids)

    #
    # Determine processing status for every attachment.
    #
    allowed_statuses = {
        AttachmentProcessingStatus.SUCCESS,
        AttachmentProcessingStatus.UNSUPPORTED,
        AttachmentProcessingStatus.EXTRACTION_FAILED,
        AttachmentProcessingStatus.DOWNLOAD_FAILED,
    }

    status_counts = {status: 0 for status in allowed_statuses}

    for item in stored_attachments:
        status = item.get("processing_status")

        assert status in allowed_statuses, (
            item.get("id"),
            item.get("filename"),
            status,
        )

        status_counts[status] += 1

    #
    # Identify successfully indexed attachments.
    #
    success_ids = {
        str(item["id"])
        for item in stored_attachments
        if item.get("processing_status") == AttachmentProcessingStatus.SUCCESS
    }

    #
    # Identify failed/unsupported attachments.
    #
    # non_success_ids = attachment_ids - success_ids

    #
    # Read all extracted content belonging to this page.
    #
    stored_contents = list(
        container.attachment_content_repository.collection.find(
            {
                "page_id": PAGE_ID,
            }
        )
    )

    #
    # An attachment can have multiple content documents:
    #
    #   199321138
    #   199321138__chunk_000001
    #   199321138__chunk_000002
    #
    # Collapse all content documents back to their root attachment ID.
    #
    content_attachment_ids = {
        _root_attachment_id(str(item["_id"])) for item in stored_contents
    }

    #
    # Every successfully indexed attachment must have at least
    # one content document.
    #
    assert content_attachment_ids == success_ids

    #
    # Every successful attachment must be marked indexed.
    #
    assert all(
        item.get("indexed") is True
        for item in stored_attachments
        if item.get("processing_status") == AttachmentProcessingStatus.SUCCESS
    )

    #
    # Every successful attachment must have a content hash.
    #
    assert all(
        item.get("content_hash")
        for item in stored_attachments
        if item.get("processing_status") == AttachmentProcessingStatus.SUCCESS
    )

    #
    # Every content document must contain a content hash.
    #
    assert all(item.get("content_hash") for item in stored_contents)

    #
    # Print a concise summary.
    #
    print()
    print("=" * 78)
    print("REAL ATTACHMENT - PAGE 199314447")
    print("=" * 78)

    print(f"Attachments discovered : {len(attachment_ids)}")

    print(f"Attachments stored     : {len(stored_attachments)}")

    print(
        f"Successful             : {status_counts[AttachmentProcessingStatus.SUCCESS]}"
    )

    print(
        f"Unsupported            : "
        f"{status_counts[AttachmentProcessingStatus.UNSUPPORTED]}"
    )

    print(
        f"Extraction failed      : "
        f"{status_counts[AttachmentProcessingStatus.EXTRACTION_FAILED]}"
    )

    print(
        f"Download failed        : "
        f"{status_counts[AttachmentProcessingStatus.DOWNLOAD_FAILED]}"
    )

    print(f"Content documents      : {len(stored_contents)}")

    print(f"Content attachments    : {len(content_attachment_ids)}")

    print("=" * 78)

    #
    # Print failures explicitly.
    #
    failures = [
        item
        for item in stored_attachments
        if item.get("processing_status") != AttachmentProcessingStatus.SUCCESS
    ]

    if failures:
        print()
        print("Attachment failures:")
        print("-" * 78)

        for item in failures:
            print(
                f"{item.get('processing_status'):20} | "
                f"{item.get('id')} | "
                f"{item.get('filename')}"
            )

            error = item.get("processing_error")

            if error:
                print(f"{'':20} | ERROR: {error}")

        print("-" * 78)

    #
    # Print status summary in a stable order.
    #
    print()
    print("Attachment processing status summary:")

    for status in (
        AttachmentProcessingStatus.SUCCESS,
        AttachmentProcessingStatus.UNSUPPORTED,
        AttachmentProcessingStatus.EXTRACTION_FAILED,
        AttachmentProcessingStatus.DOWNLOAD_FAILED,
    ):
        print(f"{status:20}: {status_counts[status]}")

    print("=" * 78)

    #
    # Sanity check:
    # every discovered attachment must have exactly one final status.
    #
    assert sum(status_counts.values()) == len(attachment_ids)

    #
    # We deliberately do NOT assert that every attachment succeeded.
    #
    # The purpose of this integration test is to verify that the
    # processing pipeline correctly persists both successful and
    # failed states.
    #
    # If an attachment is SUCCESS:
    #     content must exist.
    #
    # If an attachment fails:
    #     its failure status must be persisted.
    #
    # This allows the test to expose the exact remaining real-world
    # failures without incorrectly treating them as a content-chunk
    # counting problem.
