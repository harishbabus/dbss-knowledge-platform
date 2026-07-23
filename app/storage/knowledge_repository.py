from app.storage.mongodb import mongodb


class KnowledgeRepository:

    def __init__(self):

        self.collection = mongodb.collection("knowledge_pages")

    def save(self, knowledge_page):

        self.collection.update_one(
            {"_id": knowledge_page.id},
            {"$set": knowledge_page.model_dump()},
            upsert=True,
        )

    def count(self):

        return self.collection.count_documents({})
