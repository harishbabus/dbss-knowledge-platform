from app.models.attachment import Attachment


class AttachmentExtractor:


    def extract(
        self,
        page_id: str,
        attachments: list
    ):

        result = []


        for item in attachments:

            result.append(

                Attachment(

                    id=str(
                        item["id"]
                    ),

                    page_id=str(
                        page_id
                    ),

                    filename=item.get(
                        "filename"
                    ),

                    media_type=item.get(
                        "media_type"
                    ),

                    size=item.get(
                        "size"
                    ),

                    download_url=item.get(
                        "download_url"
                    ),

                    created_by=item.get(
                        "created_by"
                    ),

                    created_date=item.get(
                        "created_date"
                    ),

                    thumbnail_url=item.get(
                        "thumbnail_url"
                    ),

                    status=item.get(
                        "status"
                    ),

                    labels=item.get(
                        "labels",
                        []
                    ),
                    
                    version=item.get(
                        "version"
                    )

                )
            )


        return result