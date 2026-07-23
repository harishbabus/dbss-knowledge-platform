from app.extractors.page_extractor import PageExtractor
from app.extractors.attachment_extractor import AttachmentExtractor
from app.extractors.attachment_content_extractor import (
    AttachmentContentExtractor
)

from app.connectors.attachment_downloader import (
    AttachmentDownloader
)

from app.builders.knowledge_builder import (
    KnowledgeBuilder
)

from app.storage.knowledge_repository import (
    KnowledgeRepository
)

from app.storage.attachment_repository import (
    AttachmentRepository
)

from app.repositories.attachment_content_repository import (
    AttachmentContentRepository
)

from app.models.attachment_content import (
    AttachmentContent
)

from app.utils.logger import logger

import hashlib



class PageProcessor:


    def __init__(self):

        self.page_extractor = (
            PageExtractor()
        )

        self.attachment_extractor = (
            AttachmentExtractor()
        )

        self.downloader = (
            AttachmentDownloader()
        )

        self.content_extractor = (
            AttachmentContentExtractor()
        )

        self.builder = (
            KnowledgeBuilder()
        )

        self.knowledge_repo = (
            KnowledgeRepository()
        )

        self.attachment_repo = (
            AttachmentRepository()
        )

        self.content_repo = (
            AttachmentContentRepository()
        )



    def process(
        self,
        page_id,
        page_data
    ):


        logger.info(
            f"Processing page {page_id}"
        )


        #
        # Extract page
        #
        page, content = (
            self.page_extractor
            .extract(
                page_data
            )
        )


        #
        # Attachments
        #
        attachment_data = (
            page_data
            .get(
                "_attachments",
                []
            )
        )


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
        # Process attachment contents
        #
        for attachment in attachments:


            try:

                self.downloader.download(
                    attachment
                )


                extracted = (
                    self.content_extractor
                    .extract(
                        attachment
                    )
                )


                if not extracted:

                    continue



                text = (
                    extracted.get(
                        "text",
                        ""
                    )
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


                self.content_repo.save(
                    attachment_content
                )


            except Exception as e:

                logger.error(
                    f"""
Attachment failed:

{attachment.filename}

{e}
"""
                )



        #
        # Build knowledge
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


        self.knowledge_repo.save(
            knowledge_page
        )


        return knowledge_page