from app.connectors.confluence_client import ConfluenceClient

from app.extractors.page_extractor import PageExtractor
from app.extractors.attachment_extractor import AttachmentExtractor

from app.builders.knowledge_builder import KnowledgeBuilder

from app.storage.knowledge_repository import KnowledgeRepository
from app.storage.attachment_repository import AttachmentRepository

from app.utils.logger import logger



class KnowledgeCrawler:


    def __init__(self):

        self.client = ConfluenceClient()

        self.page_extractor = PageExtractor()

        self.attachment_extractor = AttachmentExtractor()

        self.builder = KnowledgeBuilder()

        self.knowledge_repo = KnowledgeRepository()

        self.attachment_repo = AttachmentRepository()



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


            pages = response.get(
                "results",
                []
            )


            if not pages:

                break



            for item in pages:


                page_id = item["id"]


                try:


                    #
                    # Fetch complete page
                    #
                    page_data = (
                        self.client
                        .get_page_details(
                            page_id
                        )
                    )



                    #
                    # Extract page + content
                    #
                    page, content = (
                        self.page_extractor
                        .extract(
                            page_data
                        )
                    )



                    #
                    # Fetch attachments
                    #
                    attachment_data = (
                        self.client
                        .get_attachments(
                            page_id
                        )
                    )



                    #
                    # Convert attachments to models
                    #
                    attachments = (
                        self.attachment_extractor
                        .extract(
                            page_id,
                            attachment_data
                        )
                    )



                    #
                    # Save attachments separately
                    #
                    self.attachment_repo.save_many(
                        attachments
                    )



                    #
                    # Build final knowledge object
                    #
                    knowledge_page = (
                        self.builder
                        .build(
                            page_data,
                            content.model_dump(),
                            [
                                a.model_dump()
                                for a in attachments
                            ]
                        )
                    )



                    #
                    # Save complete knowledge document
                    #
                    self.knowledge_repo.save(
                        knowledge_page
                    )


                    saved += 1



                except Exception as e:


                    failed += 1


                    logger.error(
                        f"Failed page {page_id}: {e}"
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

            "processed": processed,

            "saved": saved,

            "failed": failed

        }