from app.connectors.confluence_client import ConfluenceClient
from app.connectors.attachment_downloader import AttachmentDownloader

from app.extractors.page_extractor import PageExtractor
from app.extractors.attachment_extractor import AttachmentExtractor
from app.extractors.attachment_content_extractor import AttachmentContentExtractor

from app.builders.knowledge_builder import KnowledgeBuilder

from app.storage.knowledge_repository import KnowledgeRepository
from app.storage.attachment_repository import AttachmentRepository

from app.repositories.attachment_content_repository import (
    AttachmentContentRepository
)

from app.models.attachment_content import AttachmentContent

from app.utils.logger import logger

import hashlib



class KnowledgeCrawler:


    def __init__(self):

        self.client = ConfluenceClient()

        self.page_extractor = PageExtractor()

        self.attachment_extractor = AttachmentExtractor()

        self.attachment_downloader = AttachmentDownloader()

        self.attachment_content_extractor = (
            AttachmentContentExtractor()
        )

        self.builder = KnowledgeBuilder()


        self.knowledge_repo = (
            KnowledgeRepository()
        )


        self.attachment_repo = (
            AttachmentRepository()
        )


        self.attachment_content_repo = (
            AttachmentContentRepository()
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
                    # Extract page content
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
                    # Convert attachment metadata
                    #
                    attachments = (
                        self.attachment_extractor
                        .extract(
                            page_id,
                            attachment_data
                        )
                    )



                    #
                    # Save attachment metadata
                    #
                    self.attachment_repo.save_many(
                        attachments
                    )



                    #
                    # Download + extract attachment contents
                    #
                    for attachment in attachments:


                        try:


                            file_path = (
                                self.attachment_downloader
                                .download(
                                    attachment
                                )
                            )


                            extracted = (
                                self.attachment_content_extractor
                                .extract(
                                    attachment
                                )
                            )


                            if extracted:


                                text = extracted.get(
                                    "text",
                                    ""
                                )


                                content_hash = (
                                    hashlib.sha256(
                                        text.encode(
                                            "utf-8"
                                        )
                                    )
                                    .hexdigest()
                                )


                                attachment_content = (
                                    AttachmentContent(

                                        id=str(
                                            attachment.id
                                        ),

                                        page_id=str(
                                            page_id
                                        ),

                                        filename=(
                                            attachment.filename
                                        ),

                                        content_type=(
                                            extracted
                                            .get(
                                                "content_type"
                                            )
                                        ),

                                        text=text,

                                        content_hash=(
                                            content_hash
                                        )

                                    )
                                )


                                self.attachment_content_repo.save(
                                    attachment_content
                                )



                        except Exception as e:


                            logger.error(
                                f"""
Attachment processing failed:

{attachment.filename}

{e}
"""
                            )



                    #
                    # Build knowledge page
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
                    # Save knowledge page
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