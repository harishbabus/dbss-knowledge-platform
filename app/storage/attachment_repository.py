from datetime import datetime, timezone

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

        #
        # Brand new attachment
        #
        if not existing:
            logger.info(f"New attachment detected: {attachment.filename}")

            return True

        #
        # Version changed
        #
        if existing.get("version") != attachment.version:
            logger.info(f"Version changed: {attachment.filename}")

            return True

        #
        # Size changed
        #
        if existing.get("size") != attachment.size:
            logger.info(f"Size changed: {attachment.filename}")

            return True

        logger.info(f"Attachment unchanged: {attachment.filename}")

        return False

    def mark_indexed(
        self,
        attachment_id: str,
        content_hash: str,
    ) -> None:
        """
        Marks an attachment as indexed and stores
        the extracted content hash.
        """

        self.collection.update_one(
            {"id": attachment_id},
            {
                "$set": {
                    "indexed": True,
                    "content_hash": content_hash,
                    "indexed_at": datetime.now(timezone.utc),
                }
            },
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
