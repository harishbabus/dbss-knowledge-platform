import hashlib
from typing import Any

from app.extractors.page_extractor import PageExtractor
from app.extractors.attachment_extractor import AttachmentExtractor
from app.extractors.attachment_content_extractor import AttachmentContentExtractor
from app.models.attachment import Attachment
from app.models.attachment_content import AttachmentContent


from app.connectors.attachment_downloader import AttachmentDownloader

from app.builders.knowledge_builder import KnowledgeBuilder

from app.storage.knowledge_repository import KnowledgeRepository

from app.storage.attachment_repository import AttachmentRepository

from app.repositories.attachment_content_repository import AttachmentContentRepository


from app.utils.logger import logger


class PageProcessor:

    def __init__(self):

        self.page_extractor = PageExtractor()

        self.attachment_extractor = AttachmentExtractor()

        self.downloader = AttachmentDownloader()

        self.content_extractor = AttachmentContentExtractor()

        self.builder = KnowledgeBuilder()

        self.knowledge_repo = KnowledgeRepository()

        self.attachment_repo = AttachmentRepository()

        self.content_repo = AttachmentContentRepository()

    def _calculate_content_hash(
            self, 
            text: str
        ) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _create_attachment_content(
            self, 
            attachment: Attachment, 
            page_id: str, 
            extracted: dict[str, Any]
        ) -> AttachmentContent:
        """
        Creates an AttachmentContent model from
        extracted attachment data.
        """

        text = extracted.get("text", "")

        return AttachmentContent(
            id=str(attachment.id),
            page_id=str(page_id),
            filename=attachment.filename,
            file_path=extracted.get("file_path"),
            content_type=extracted.get("content_type"),
            text=text,
            content_hash=self._calculate_content_hash(text),
        )

    def _save_attachment_content(self, attachment, attachment_content):
        self.content_repo.save(attachment_content)

        self.attachment_repo.mark_indexed(
            attachment.id, attachment_content.content_hash
        )

    def _process_attachment(
            self, 
            attachment: Attachment, 
            page_id: str,
        ) -> None:
        """
        Downloads, extracts and stores
        one attachment.
        """

        try:

            self.downloader.download(attachment)

            extracted = self.content_extractor.extract(attachment)

            if not extracted:
                logger.warning(f"No extractor for {attachment.filename}")

                return

            attachment_content = self._create_attachment_content(
                attachment, page_id, extracted
            )

            self._save_attachment_content(attachment, attachment_content)

            logger.info(f"Indexed {attachment.filename}")

        except Exception as e:

            logger.exception(f"""
    Attachment failed

    {attachment.filename}

    {e}
    """)

    def _delete_removed_attachments(
            self, 
            existing_map: dict[str, dict[str, Any]], 
            attachments: list[Attachment]
    ) -> int:
        """
        Remove attachments that no longer exist in Confluence.
        """

        current_ids = {attachment.id for attachment in attachments}

        deleted_ids = set(existing_map.keys()) - current_ids

        for attachment_id in deleted_ids:

            self.attachment_repo.delete(attachment_id)

            self.content_repo.delete(attachment_id)

            logger.info(f"Deleted attachment {attachment_id}")

        return len(deleted_ids)

    def _get_attachments_to_process(
            self, 
            attachments: list[Attachment], 
            existing_map: dict[str, dict[str, Any]]
    ) -> list[Attachment]:
        """
        Returns attachments that require processing.
        """

        attachments_to_process = []

        for attachment in attachments:

            existing_attachment = existing_map.get(attachment.id)

            #
            # New attachment
            #
            if existing_attachment is None:

                self._queue_attachment_for_processing(
                    attachment, "New attachment", attachments_to_process
                )

                continue

            #
            # Version changed
            #
            if existing_attachment.get("version") != attachment.version:

                self._queue_attachment_for_processing(
                    attachment, "Version changed", attachments_to_process
                )

                continue

            #
            # Size changed
            #
            if existing_attachment.get("size") != attachment.size:

                self._queue_attachment_for_processing(
                    attachment, "Size changed", attachments_to_process
                )

                continue

        return attachments_to_process

    def _queue_attachment_for_processing(
        self,
        attachment: Attachment,
        reason: str,
        attachments_to_process: list[Attachment],
    ) -> None:

        logger.info(f"{reason}: {attachment.filename}")

        attachments_to_process.append(attachment)

    def _process_attachments(
            self, 
            attachments: list[Attachment], 
            page_id: str
        ) -> None:
        """
        Process all attachments that require indexing.
        """

        for attachment in attachments:

            logger.info(f"Extracting {attachment.filename}")

            self._process_attachment(attachment=attachment, page_id=page_id)

    def _load_existing_attachments(
            self, 
            page_id
        ) -> dict[str, dict[str, Any]]:
        """
        Loads all indexed attachments for a page and
        returns them as a dictionary keyed by attachment id.
        """

        existing_attachments = self.attachment_repo.get_by_page(page_id)

        return {item["id"]: item for item in existing_attachments}

    def _prepare_attachment_data(
            self, 
            attachments: list[Attachment]
        ) -> list[dict[str, Any]]:
        """
        Converts attachment models into dictionaries
        expected by the knowledge builder.
        """

        return [attachment.model_dump() for attachment in attachments]

    def process(self, page_id, page_data):

        logger.info(f"Processing page {page_id}")

        #
        # Extract page
        #
        page, content = self.page_extractor.extract(page_data)

        #
        # Extract attachment metadata
        #
        attachment_data = page_data.get("_attachments", [])

        attachments = self.attachment_extractor.extract(page_id, attachment_data)

        ####################################################
        # Load existing attachments ONCE
        ####################################################

        existing_map = self._load_existing_attachments(page_id)

        ####################################################
        # Detect deleted attachments
        ####################################################

        deleted_count = self._delete_removed_attachments(existing_map, attachments)

        ####################################################
        # Detect changed attachments
        ####################################################

        attachments_to_process = self._get_attachments_to_process(
            attachments, existing_map
        )

        ####################################################
        # Save metadata
        ####################################################

        self.attachment_repo.save_many(attachments)

        ####################################################
        # Process changed attachments
        ####################################################

        self._process_attachments(attachments_to_process, page_id)

        ####################################################
        # Statistics
        ####################################################

        logger.info(f"""
Page Summary

Attachments found      : {len(attachments)}
Processed attachments  : {len(attachments_to_process)}
Skipped attachments    : {len(attachments)-len(attachments_to_process)}
Deleted attachments    : {deleted_count}
""")

        ####################################################
        # Build knowledge page
        ####################################################

        knowledge_page = self.builder.build(
            page_data, content.model_dump(), self._prepare_attachment_data(attachments)
        )

        self.knowledge_repo.save(knowledge_page)

        logger.info(f"Finished page {page_id}")

        return knowledge_page
