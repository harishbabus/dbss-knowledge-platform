from app.storage.mongodb import mongodb


class SyncRepository:

    def __init__(self):

        self.collection = mongodb.collection("sync_metadata")

    def get_last_sync_time(self):

        data = self.collection.find_one({"_id": "confluence_sync"})

        if data:

            return data.get("last_sync_time")

        return None

    def update_sync_time(self, sync_time):

        self.collection.update_one(
            {"_id": "confluence_sync"},
            {"$set": {"last_sync_time": sync_time, "status": "SUCCESS"}},
            upsert=True,
        )
