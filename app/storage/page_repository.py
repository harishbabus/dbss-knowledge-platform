from pymongo.collection import Collection

from app.storage.mongodb import mongodb
from app.utils.logger import logger


class PageRepository:

    def __init__(self):

        self.collection: Collection = mongodb.collection(
            "pages"
        )

    def save_page(self, page):

        document = page.model_dump()

        document["_id"] = document.pop("id")

        result = self.collection.replace_one(
            {
                "_id": document["_id"]
            },
            document,
            upsert=True
        )

        if result.upserted_id:
            return "INSERT"

        if result.modified_count:
            return "UPDATE"

        return "UNCHANGED"

    def count(self):

        return self.collection.count_documents({})

    def find_by_page_id(self, page_id):

        return self.collection.find_one(
            {
                "id": page_id
            }
        )

    def delete_all(self):

        result = self.collection.delete_many({})

        logger.info(
            f"Deleted {result.deleted_count} pages"
        )