from datetime import datetime

from app.storage.mongodb import mongodb


class CrawlerStateRepository:

    def __init__(self):

        self.collection = mongodb.collection("crawler_state")

    def get(self):

        return self.collection.find_one({"_id": "crawler"})

    def save(self):

        self.collection.update_one(
            {"_id": "crawler"}, {"$set": {"last_crawl": datetime.utcnow()}}, upsert=True
        )
