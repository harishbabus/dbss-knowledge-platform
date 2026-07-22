from app.storage.mongodb import mongodb


class PageRepository:


    def __init__(self):

        self.collection = (
            mongodb.collection(
                "pages"
            )
        )


    def save(
        self,
        page
    ):

        self.collection.update_one(

            {
                "_id": page.id
            },

            {
                "$set":
                page.model_dump()
            },

            upsert=True
        )



    def exists(
        self,
        page_id
    ):

        return (
            self.collection
            .find_one(
                {
                    "_id": page_id
                }
            )
            is not None
        )



    def get(
        self,
        page_id
    ):

        return (
            self.collection
            .find_one(
                {
                    "_id": page_id
                }
            )
        )



    def count(self):

        return (
            self.collection
            .count_documents({})
        )