from app.connectors.confluence_client import (
    ConfluenceClient
)

from app.services.page_processor import (
    PageProcessor
)

from app.utils.logger import (
    logger
)



class KnowledgeCrawler:


    def __init__(self):


        self.client = (
            ConfluenceClient()
        )


        self.processor = (
            PageProcessor()
        )



    def run(
        self,
        batch_size=100
    ):


        start = 0

        processed = 0

        saved = 0

        failed = 0



        while True:


            logger.info(
                f"Fetching pages start={start}"
            )



            response = (
                self.client
                .get_pages(
                    start=start,
                    limit=batch_size
                )
            )



            pages = (
                response
                .get(
                    "results",
                    []
                )
            )



            if not pages:

                break



            for item in pages:


                page_id = (
                    item["id"]
                )


                try:


                    #
                    # Fetch complete page details
                    #
                    page_data = (
                        self.client
                        .get_page_details(
                            page_id
                        )
                    )



                    #
                    # Process page completely
                    #
                    # Includes:
                    # - page extraction
                    # - attachment extraction
                    # - attachment download
                    # - content extraction
                    # - OCR images
                    # - attachment_contents save
                    # - knowledge save
                    #
                    self.processor.process(
                        page_id,
                        page_data
                    )


                    saved += 1



                except Exception as e:


                    failed += 1


                    logger.error(
                        f"""
Failed page {page_id}

{e}
"""
                    )



                processed += 1



            start += batch_size



            logger.info(
                f"""
Progress:

Processed : {processed}
Saved     : {saved}
Failed    : {failed}

"""
            )



        return {


            "processed":
                processed,


            "saved":
                saved,


            "failed":
                failed

        }