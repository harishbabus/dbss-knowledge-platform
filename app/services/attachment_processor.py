from __future__ import annotations
import hashlib
from app.extractors.attachment_content_extractor import AttachmentContentExtractor
from app.connectors.attachment_downloader import AttachmentDownloader
from app.models.attachment import Attachment
from app.models.attachment_content import AttachmentContent
from app.storage.attachment_repository import AttachmentRepository
from app.repositories.attachment_content_repository import (
    AttachmentContentRepository,
)
from app.utils.logger import logger
from app.models.extracted_content import ExtractedContent


class AttachmentProcessor:
    """
    Processes a single attachment.

    Responsibilities

    - download
    - extract
    - hash
    - create AttachmentContent
    - persist
    - mark indexed
    """

    def __init__(
        self,
        attachment_repo: AttachmentRepository,
        content_repo: AttachmentContentRepository,
        downloader: AttachmentDownloader,
        content_extractor: AttachmentContentExtractor,
    ):
        self.downloader = downloader

        self.content_extractor = content_extractor

        self.attachment_repo = attachment_repo

        self.content_repo = content_repo

    def process(
        self,
        attachment: Attachment,
        page_id: str,
    ) -> None:
        try:
            self.downloader.download(attachment)

            extracted = self.content_extractor.extract(attachment)

            if not extracted:
                logger.warning(f"No extractor for {attachment.filename}")

                return

            attachment_content = self._create_attachment_content(
                attachment,
                page_id,
                extracted,
            )

            self._save_attachment_content(
                attachment,
                attachment_content,
            )

            logger.info(f"Indexed {attachment.filename}")

        except Exception:
            logger.exception(f"""
Attachment failed

{attachment.filename}
""")

    def _create_attachment_content(
        self,
        attachment: Attachment,
        page_id: str,
        extracted: ExtractedContent,
    ) -> AttachmentContent:
        return AttachmentContent(
            id=str(attachment.id),
            page_id=str(page_id),
            filename=attachment.filename,
            file_path=extracted.file_path,
            content_type=extracted.content_type,
            text=extracted.text,
            content_hash=self._calculate_content_hash(extracted.text),
        )

    def _save_attachment_content(
        self,
        attachment: Attachment,
        attachment_content: AttachmentContent,
    ) -> None:
        self.content_repo.save(attachment_content)

        self.attachment_repo.mark_indexed(
            attachment.id,
            attachment_content.content_hash,
        )

    @staticmethod
    def _calculate_content_hash(
        text: str,
    ) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def delete(self, attachment_id: str) -> None:
        self.attachment_repo.delete(attachment_id)

        self.content_repo.delete(attachment_id)
