from app.storage.mongodb import mongodb


class SyncCheckpointRepository:


    def __init__(self):

        self.collection = (
            mongodb.collection(
                "sync_checkpoint"
            )
        )


    def get(
        self,
        sync_id
    ):

        return (
            self.collection
            .find_one(
                {
                    "_id": sync_id
                }
            )
        )


    def save(
        self,
        checkpoint
    ):

        self.collection.update_one(

            {
                "_id": checkpoint.id
            },

            {
                "$set":
                checkpoint.model_dump()
            },

            upsert=True
        )