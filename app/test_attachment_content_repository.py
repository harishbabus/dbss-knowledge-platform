from unittest.mock import MagicMock

from app.models.attachment_content import AttachmentContent
from app.repositories.attachment_content_repository import (
    AttachmentContentRepository,
)


def _content(text: str) -> AttachmentContent:
    return AttachmentContent(
        id="att-1",
        page_id="page-1",
        filename="sample.txt",
        content_type="text",
        text=text,
        file_path="downloads/sample.txt",
        content_hash="hash-1",
    )


def test_save_small_content_uses_attachment_id_as_first_document_id():
    repository = AttachmentContentRepository()
    repository.collection = MagicMock()

    repository.save(_content("hello"))

    repository.collection.delete_many.assert_called_once_with(
        {"attachment_id": "att-1"}
    )

    repository.collection.insert_many.assert_called_once()

    documents = repository.collection.insert_many.call_args.args[0]

    assert len(documents) == 1
    assert documents[0]["_id"] == "att-1"
    assert documents[0]["attachment_id"] == "att-1"
    assert documents[0]["chunk_index"] == 0
    assert documents[0]["chunk_count"] == 1
    assert documents[0]["is_chunked"] is False
    assert documents[0]["text"] == "hello"


def test_save_large_content_creates_ordered_chunks():
    repository = AttachmentContentRepository()
    repository.collection = MagicMock()

    size = repository.MAX_TEXT_CHARS_PER_CHUNK
    text = "A" * (size * 2 + 10)

    repository.save(_content(text))

    documents = repository.collection.insert_many.call_args.args[0]

    assert len(documents) == 3

    assert documents[0]["_id"] == "att-1"
    assert documents[1]["_id"] == "att-1__chunk_000001"
    assert documents[2]["_id"] == "att-1__chunk_000002"

    assert [item["chunk_index"] for item in documents] == [0, 1, 2]
    assert all(item["chunk_count"] == 3 for item in documents)
    assert all(item["is_chunked"] is True for item in documents)

    reconstructed = "".join(item["text"] for item in documents)

    assert reconstructed == text


def test_delete_removes_all_chunks():
    repository = AttachmentContentRepository()
    repository.collection = MagicMock()

    repository.delete("att-1")

    repository.collection.delete_many.assert_called_once_with(
        {"attachment_id": "att-1"}
    )

    repository.collection.delete_one.assert_called_once_with({"_id": "att-1"})


def test_split_text_does_not_lose_content():
    repository = AttachmentContentRepository()

    text = "0123456789" * 100

    chunks = repository._split_text(text)

    assert "".join(chunks) == text
    assert all(len(chunk) <= repository.MAX_TEXT_CHARS_PER_CHUNK for chunk in chunks)
