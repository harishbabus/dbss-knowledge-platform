from app.storage.mongodb import mongodb


class ContentRepository:


    def __init__(self):

        self.collection = (
            mongodb.collection(
                "page_content"
            )
        )


    def save(
        self,
        content
    ):

        self.collection.update_one(

            {
                "_id":
                content.page_id
            },

            {
                "$set":
                self._sanitize(
                    content.model_dump()
                )
            },

            upsert=True
        )



    def get_hash(
        self,
        page_id
    ):

        document = (
            self.collection
            .find_one(
                {
                    "_id":
                    page_id
                },
                {
                    "content_hash":1
                }
            )
        )


        if document:

            return document.get(
                "content_hash"
            )


        return None



    def count(self):

        return (
            self.collection
            .count_documents({})
        )

    def _sanitize(
        self,
        obj
    ):

        if isinstance(
            obj,
            dict
        ):

            return {
                k:self._sanitize(v)
                for k,v in obj.items()
            }


        if isinstance(
            obj,
            list
        ):

            return [
                self._sanitize(x)
                for x in obj
            ]


        if not isinstance(
            obj,
            (str,int,float,bool,type(None))
        ):

            return str(obj)


        return obj