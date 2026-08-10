from datetime import datetime, timezone

from app.models.attachment_processing_result import AttachmentProcessingStatus
from app.storage.mongodb import mongodb
from app.utils.logger import logger


class AttachmentRepository:
    def __init__(self):
        self.collection = mongodb.collection("attachments")

    def save(self, attachment):
        logger.info(f"Saving attachment: {attachment.id} {attachment.filename}")

        document = attachment.model_dump()

        document["updated_at"] = datetime.now(timezone.utc)

        result = self.collection.update_one(
            {"id": attachment.id}, {"$set": document}, upsert=True
        )

        logger.info(
            f"Matched={result.matched_count}, "
            f"Modified={result.modified_count}, "
            f"Upserted={result.upserted_id}"
        )

    def save_many(self, attachments):
        for attachment in attachments:
            self.save(attachment)

    def get(self, attachment_id):
        return self.collection.find_one({"id": attachment_id})

    def exists(self, attachment_id):
        return self.collection.count_documents({"id": attachment_id}, limit=1) > 0

    def get_by_page(self, page_id):
        return list(self.collection.find({"page_id": page_id}))

    def needs_processing(self, attachment):
        existing = self.get(attachment.id)

        if not existing:
            logger.info(f"New attachment detected: {attachment.filename}")
            return True

        if existing.get("version") != attachment.version:
            logger.info(f"Version changed: {attachment.filename}")
            return True

        if existing.get("size") != attachment.size:
            logger.info(f"Size changed: {attachment.filename}")
            return True

        status = existing.get("processing_status")
        if status in {
            AttachmentProcessingStatus.DOWNLOAD_FAILED,
            AttachmentProcessingStatus.EXTRACTION_FAILED,
        }:
            logger.info(
                f"Retrying attachment with previous status {status}: "
                f"{attachment.filename}"
            )
            return True

        if status == AttachmentProcessingStatus.UNSUPPORTED:
            logger.info(
                f"Attachment unsupported and will not be retried: {attachment.filename}"
            )
            return False

        # Same version and size with no retryable failure is unchanged.
        # Do not require an `indexed` flag here: older attachment records
        # predate processing_status/indexed and remain valid unchanged records.
        logger.info(f"Attachment unchanged: {attachment.filename}")
        return False

    def mark_downloaded(
        self,
        attachment_id: str,
        file_path: str,
        size: int | None,
        content_hash: str | None,
    ) -> None:
        self.collection.update_one(
            {"id": attachment_id},
            {
                "$set": {
                    "downloaded_path": file_path,
                    "size": size,
                    "download_hash": content_hash,
                    "last_downloaded": datetime.now(timezone.utc),
                    "processing_status": None,
                    "processing_error": None,
                }
            },
        )

    def mark_processing_status(
        self,
        attachment_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        self.collection.update_one(
            {"id": attachment_id},
            {
                "$set": {
                    "indexed": False,
                    "processing_status": status,
                    "processing_error": error,
                    "last_processed": datetime.now(timezone.utc),
                }
            },
        )

    def mark_indexed(
        self,
        attachment_id: str,
        content_hash: str,
    ) -> None:
        self.collection.update_one(
            {"id": attachment_id},
            {
                "$set": {
                    "indexed": True,
                    "content_hash": content_hash,
                    "processing_status": "SUCCESS",
                    "processing_error": None,
                    "last_processed": datetime.now(timezone.utc),
                    "indexed_at": datetime.now(timezone.utc),
                }
            },
        )

    def get_retryable_by_page(self, page_id: str) -> list[dict]:
        """Return attachments on a page that are eligible for automatic retry."""
        return list(
            self.collection.find(
                {
                    "page_id": str(page_id),
                    "processing_status": {
                        "$in": [
                            AttachmentProcessingStatus.DOWNLOAD_FAILED,
                            AttachmentProcessingStatus.EXTRACTION_FAILED,
                        ]
                    },
                }
            )
        )

    def has_retryable_by_page(self, page_id: str) -> bool:
        """Return True when a page has an attachment eligible for retry."""
        return (
            self.collection.count_documents(
                {
                    "page_id": str(page_id),
                    "processing_status": {
                        "$in": [
                            AttachmentProcessingStatus.DOWNLOAD_FAILED,
                            AttachmentProcessingStatus.EXTRACTION_FAILED,
                        ]
                    },
                },
                limit=1,
            )
            > 0
        )

    def delete(self, attachment_id):
        result = self.collection.delete_one({"id": attachment_id})

        logger.info(f"Deleted attachments: {result.deleted_count}")

    def delete_missing(self, page_id, current_attachment_ids):
        stored = self.collection.find({"page_id": page_id}, {"id": 1})

        stored_ids = {item["id"] for item in stored}

        missing = stored_ids - set(current_attachment_ids)

        if not missing:
            return []

        self.collection.delete_many({"id": {"$in": list(missing)}})

        logger.info(f"Deleted {len(missing)} obsolete attachments")

        return list(missing)

    def count(self):
        return self.collection.count_documents({})
