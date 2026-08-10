from unittest.mock import MagicMock

from app.models.attachment import Attachment
from app.storage.attachment_repository import AttachmentRepository


def _attachment(
    attachment_id="att-1",
    page_id="page-1",
    filename="test.pdf",
    version=1,
    size=100,
):
    return Attachment(
        id=attachment_id,
        page_id=page_id,
        filename=filename,
        media_type="application/pdf",
        size=size,
        version=version,
        download_url="https://example.com/test.pdf",
    )


def test_save_uses_upsert():
    repository = AttachmentRepository()

    repository.collection = MagicMock()

    attachment = _attachment()

    repository.save(attachment)

    repository.collection.update_one.assert_called_once()

    args, kwargs = repository.collection.update_one.call_args

    assert args[0] == {"id": "att-1"}
    assert kwargs["upsert"] is True


def test_get_reads_attachment():
    repository = AttachmentRepository()

    repository.collection = MagicMock()

    repository.collection.find_one.return_value = {
        "id": "att-1",
        "page_id": "page-1",
    }

    result = repository.get("att-1")

    repository.collection.find_one.assert_called_once_with({"id": "att-1"})

    assert result["id"] == "att-1"


def test_exists_returns_true_for_existing_attachment():
    repository = AttachmentRepository()

    repository.collection = MagicMock()

    repository.collection.count_documents.return_value = 1

    assert repository.exists("att-1") is True

    repository.collection.count_documents.assert_called_once_with(
        {"id": "att-1"},
        limit=1,
    )


def test_exists_returns_false_for_missing_attachment():
    repository = AttachmentRepository()

    repository.collection = MagicMock()

    repository.collection.count_documents.return_value = 0

    assert repository.exists("att-1") is False


def test_get_by_page():
    repository = AttachmentRepository()

    repository.collection = MagicMock()

    repository.collection.find.return_value = [
        {"id": "att-1", "page_id": "page-1"},
        {"id": "att-2", "page_id": "page-1"},
    ]

    result = repository.get_by_page("page-1")

    repository.collection.find.assert_called_once_with({"page_id": "page-1"})

    assert len(result) == 2


def test_needs_processing_for_new_attachment():
    repository = AttachmentRepository()

    repository.get = MagicMock(return_value=None)

    attachment = _attachment()

    assert repository.needs_processing(attachment) is True

    repository.get.assert_called_once_with("att-1")


def test_needs_processing_for_same_version_and_size():
    repository = AttachmentRepository()

    repository.get = MagicMock(
        return_value={
            "id": "att-1",
            "version": 1,
            "size": 100,
        }
    )

    attachment = _attachment(
        version=1,
        size=100,
    )

    assert repository.needs_processing(attachment) is False


def test_needs_processing_for_changed_version():
    repository = AttachmentRepository()

    repository.get = MagicMock(
        return_value={
            "id": "att-1",
            "version": 1,
            "size": 100,
        }
    )

    attachment = _attachment(
        version=2,
        size=100,
    )

    assert repository.needs_processing(attachment) is True


def test_needs_processing_for_changed_size():
    repository = AttachmentRepository()

    repository.get = MagicMock(
        return_value={
            "id": "att-1",
            "version": 1,
            "size": 100,
        }
    )

    attachment = _attachment(
        version=1,
        size=200,
    )

    assert repository.needs_processing(attachment) is True


def test_mark_indexed():
    repository = AttachmentRepository()

    repository.collection = MagicMock()

    repository.mark_indexed(
        attachment_id="att-1",
        content_hash="abc123",
    )

    repository.collection.update_one.assert_called_once()

    args, kwargs = repository.collection.update_one.call_args

    assert args[0] == {"id": "att-1"}

    update = args[1]["$set"]

    assert update["indexed"] is True
    assert update["content_hash"] == "abc123"
    assert "indexed_at" in update


def test_delete():
    repository = AttachmentRepository()

    repository.collection = MagicMock()

    repository.delete("att-1")

    repository.collection.delete_one.assert_called_once_with({"id": "att-1"})


def test_delete_missing():
    repository = AttachmentRepository()

    repository.collection = MagicMock()

    repository.collection.find.return_value = [
        {"id": "att-1"},
        {"id": "att-2"},
        {"id": "att-3"},
    ]

    repository.delete_missing(
        page_id="page-1",
        current_attachment_ids=[
            "att-1",
            "att-3",
        ],
    )

    repository.collection.find.assert_called_once_with(
        {"page_id": "page-1"},
        {"id": 1},
    )

    repository.collection.delete_many.assert_called_once_with(
        {"id": {"$in": ["att-2"]}}
    )


def test_mark_processing_status():
    repository = AttachmentRepository()
    repository.collection = MagicMock()
    repository.mark_processing_status("att-1", "UNSUPPORTED", "No extractor")
    args, _ = repository.collection.update_one.call_args
    assert args[0] == {"id": "att-1"}
    assert args[1]["$set"]["processing_status"] == "UNSUPPORTED"
    assert args[1]["$set"]["processing_error"] == "No extractor"


def test_needs_processing_retries_failed_status():
    repository = AttachmentRepository()
    repository.get = MagicMock(
        return_value={
            "id": "att-1",
            "version": 1,
            "size": 100,
            "processing_status": "EXTRACTION_FAILED",
            "indexed": False,
        }
    )
    assert repository.needs_processing(_attachment()) is True


def test_needs_processing_does_not_retry_unsupported():
    repository = AttachmentRepository()
    repository.get = MagicMock(
        return_value={
            "id": "att-1",
            "version": 1,
            "size": 100,
            "processing_status": "UNSUPPORTED",
            "indexed": False,
        }
    )

    assert repository.needs_processing(_attachment()) is False


def test_get_retryable_by_page_filters_retryable_statuses():
    repository = AttachmentRepository()
    repository.collection = MagicMock()
    repository.collection.find.return_value = [
        {"id": "att-1", "processing_status": "DOWNLOAD_FAILED"},
    ]

    result = repository.get_retryable_by_page("page-1")

    repository.collection.find.assert_called_once_with(
        {
            "page_id": "page-1",
            "processing_status": {"$in": ["DOWNLOAD_FAILED", "EXTRACTION_FAILED"]},
        }
    )
    assert result[0]["id"] == "att-1"


def test_has_retryable_by_page_returns_true():
    repository = AttachmentRepository()
    repository.collection = MagicMock()
    repository.collection.count_documents.return_value = 1

    assert repository.has_retryable_by_page("page-1") is True
    repository.collection.count_documents.assert_called_once_with(
        {
            "page_id": "page-1",
            "processing_status": {"$in": ["DOWNLOAD_FAILED", "EXTRACTION_FAILED"]},
        },
        limit=1,
    )
