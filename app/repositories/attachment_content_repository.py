from __future__ import annotations

from app.models.attachment_content import AttachmentContent
from app.storage.mongodb import mongodb


class AttachmentContentRepository:
    """
    Persists extracted attachment content without allowing a single MongoDB
    document to grow beyond a safe BSON size.

    Small attachments remain compatible with the previous representation:
    the first/only document uses ``_id == attachment_id``.

    Large attachments are stored as multiple documents in the same
    ``attachment_contents`` collection. All chunks carry ``attachment_id``
    plus deterministic ordering metadata so the complete content can be
    reconstructed in sequence.
    """

    # Character count, deliberately well below MongoDB's 16 MB BSON limit.
    # Even for multi-byte UTF-8 text this leaves substantial room for the
    # document metadata.
    MAX_TEXT_CHARS_PER_CHUNK = 256 * 1024

    def __init__(self):
        self.collection = mongodb.collection("attachment_contents")

    def save(self, content: AttachmentContent) -> None:
        """
        Replace all previously persisted content chunks for an attachment.

        This makes retries/idempotent re-processing deterministic: stale
        chunks from an older, longer version cannot remain in MongoDB.
        """

        attachment_id = str(content.id)
        text = content.text or ""

        chunks = self._split_text(text)
        chunk_count = len(chunks)

        self.collection.delete_many({"attachment_id": attachment_id})

        documents = []

        for index, chunk_text in enumerate(chunks):
            document = content.model_dump()
            document["id"] = attachment_id
            document["_id"] = self._chunk_id(attachment_id, index)
            document["attachment_id"] = attachment_id
            document["text"] = chunk_text
            document["chunk_index"] = index
            document["chunk_count"] = chunk_count
            document["is_chunked"] = chunk_count > 1

            documents.append(document)

        self.collection.insert_many(documents)

    def delete(self, attachment_id: str) -> None:
        """Delete every persisted content chunk for an attachment."""

        attachment_id = str(attachment_id)

        self.collection.delete_many({"attachment_id": attachment_id})

        # Backward compatibility for documents created by the old
        # single-document implementation.
        self.collection.delete_one({"_id": attachment_id})

    def get(self, attachment_id: str) -> dict | None:
        """Return the first/only content document for compatibility."""

        return self.collection.find_one(
            {
                "$or": [
                    {"attachment_id": str(attachment_id), "chunk_index": 0},
                    {"_id": str(attachment_id)},
                ]
            }
        )

    def get_chunks(self, attachment_id: str) -> list[dict]:
        """Return all content chunks in deterministic order."""

        return list(
            self.collection.find({"attachment_id": str(attachment_id)}).sort(
                "chunk_index", 1
            )
        )

    def count_for_attachment(self, attachment_id: str) -> int:
        return self.collection.count_documents({"attachment_id": str(attachment_id)})

    def reconstruct_text(self, attachment_id: str) -> str:
        """Reconstruct the complete extracted text from persisted chunks."""

        chunks = self.get_chunks(attachment_id)

        if chunks:
            return "".join(chunk.get("text") or "" for chunk in chunks)

        # Backward compatibility with old single-document records.
        legacy = self.collection.find_one({"_id": str(attachment_id)})
        return (legacy or {}).get("text") or ""

    def count(self) -> int:
        return self.collection.count_documents({})

    @classmethod
    def _split_text(cls, text: str) -> list[str]:
        if not text:
            return [""]

        size = cls.MAX_TEXT_CHARS_PER_CHUNK

        return [text[start : start + size] for start in range(0, len(text), size)]

    @staticmethod
    def _chunk_id(attachment_id: str, index: int) -> str:
        if index == 0:
            return attachment_id

        return f"{attachment_id}__chunk_{index:06d}"
