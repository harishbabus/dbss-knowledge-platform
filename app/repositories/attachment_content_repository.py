from app.storage.mongodb import mongodb


class AttachmentContentRepository:

    def __init__(self):

        self.collection = mongodb.collection("attachment_contents")

    def save(self, content):

        self.collection.update_one(
            {"_id": content.id}, {"$set": content.model_dump()}, upsert=True
        )

    def count(self):

        return self.collection.count_documents({})
