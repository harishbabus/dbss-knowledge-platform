from typing import Any

from app.extractors.page_extractor import PageExtractor
from app.extractors.attachment_extractor import AttachmentExtractor
from app.models.attachment import Attachment

from app.builders.knowledge_builder import KnowledgeBuilder

from app.storage.knowledge_repository import KnowledgeRepository

from app.storage.attachment_repository import AttachmentRepository

from app.services.attachment_processor import AttachmentProcessor

from app.utils.logger import logger


class PageProcessor:
    def __init__(self):
        self.page_extractor = PageExtractor()

        self.attachment_extractor = AttachmentExtractor()

        self.builder = KnowledgeBuilder()

        self.knowledge_repo = KnowledgeRepository()

        self.attachment_repo = AttachmentRepository()

        self.attachment_processor = AttachmentProcessor()

    def _delete_removed_attachments(
        self, existing_map: dict[str, dict[str, Any]], attachments: list[Attachment]
    ) -> int:
        """
        Remove attachments that no longer exist in Confluence.
        """

        current_ids = {attachment.id for attachment in attachments}

        deleted_ids = set(existing_map.keys()) - current_ids

        for attachment_id in deleted_ids:
            self.attachment_processor.delete(attachment_id)

            logger.info(f"Deleted attachment {attachment_id}")

        return len(deleted_ids)

    def _get_attachments_to_process(
        self, attachments: list[Attachment], existing_map: dict[str, dict[str, Any]]
    ) -> list[Attachment]:
        """
        Returns attachments that require processing.
        """

        attachments_to_process: list[Attachment] = []

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

    def _process_attachments(self, attachments: list[Attachment], page_id: str) -> None:
        """
        Process all attachments that require indexing.
        """

        for attachment in attachments:
            logger.info(f"Extracting {attachment.filename}")

            self.attachment_processor.process(
                attachment,
                page_id,
            )

    def _load_existing_attachments(self, page_id) -> dict[str, dict[str, Any]]:
        """
        Loads all indexed attachments for a page and
        returns them as a dictionary keyed by attachment id.
        """

        existing_attachments = self.attachment_repo.get_by_page(page_id)

        return {item["id"]: item for item in existing_attachments}

    def _prepare_attachment_data(
        self, attachments: list[Attachment]
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
Skipped attachments    : {len(attachments) - len(attachments_to_process)}
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
