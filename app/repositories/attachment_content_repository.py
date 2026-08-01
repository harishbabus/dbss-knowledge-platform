from app.storage.mongodb import mongodb


class AttachmentContentRepository:
    def __init__(self):
        self.collection = mongodb.collection("attachment_contents")

    def save(
        self,
        content,
    ) -> None:
        self.collection.update_one(
            {"_id": content.id},
            {"$set": content.model_dump()},
            upsert=True,
        )

    def delete(
        self,
        attachment_id: str,
    ) -> None:
        """
        Deletes the extracted content for an attachment.
        """

        self.collection.delete_one({"_id": attachment_id})

    def count(
        self,
    ) -> int:
        return self.collection.count_documents({})
