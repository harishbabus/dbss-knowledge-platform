from app.storage.mongodb import mongodb
from app.utils.logger import logger


class AttachmentRepository:

    def __init__(self):

        self.collection = mongodb.collection("attachments")

    def save(self, attachment):

        logger.info(f"Saving attachment: {attachment.id} {attachment.filename}")

        result = self.collection.update_one(
            {"id": attachment.id}, {"$set": attachment.model_dump()}, upsert=True
        )

        logger.info(
            f"Matched={result.matched_count}, "
            f"Modified={result.modified_count}, "
            f"Upserted={result.upserted_id}"
        )

    def save_many(self, attachments):

        for attachment in attachments:

            self.save(attachment)

    def count(self):

        return self.collection.count_documents({})
