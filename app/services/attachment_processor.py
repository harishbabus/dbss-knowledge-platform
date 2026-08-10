from __future__ import annotations

import hashlib

from app.connectors.attachment_downloader import AttachmentDownloader
from app.extractors.attachment_content_extractor import AttachmentContentExtractor
from app.models.attachment import Attachment
from app.models.attachment_content import AttachmentContent
from app.models.extracted_content import ExtractedContent
from app.models.attachment_processing_result import (
    AttachmentProcessingResult,
    AttachmentProcessingStatus,
)
from app.repositories.attachment_content_repository import AttachmentContentRepository
from app.storage.attachment_repository import AttachmentRepository
from app.utils.logger import logger


class AttachmentProcessor:
    """Download, extract and persist one attachment with explicit outcome state."""

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
    ) -> AttachmentProcessingResult:
        attachment_id = str(attachment.id)

        try:
            download_result = self.downloader.download_with_metadata(attachment)
        except Exception as exc:
            return self._failure(
                attachment,
                AttachmentProcessingStatus.DOWNLOAD_FAILED,
                str(exc),
            )

        if download_result is None:
            return self._failure(
                attachment,
                AttachmentProcessingStatus.DOWNLOAD_FAILED,
                "Downloader returned no result",
            )

        self.attachment_repo.mark_downloaded(
            attachment_id,
            file_path=str(download_result.file_path),
            size=download_result.size,
            content_hash=download_result.content_hash,
        )

        status, extracted, error = self.content_extractor.extract_with_status(
            attachment,
            file_path=download_result.file_path,
        )

        if status != AttachmentProcessingStatus.SUCCESS or extracted is None:
            return self._failure(
                attachment,
                status,
                error or "Extractor returned no content",
            )

        attachment_content = self._create_attachment_content(
            attachment,
            page_id,
            extracted,
        )

        #
        # AttachmentContentRepository transparently stores small content
        # as one document and large content as ordered chunks. The complete
        # content hash remains the attachment-level hash.
        #
        self.content_repo.save(attachment_content)

        self.attachment_repo.mark_indexed(
            attachment_id,
            attachment_content.content_hash,
        )

        logger.info(f"Indexed {attachment.filename}")

        return AttachmentProcessingResult(
            attachment_id=attachment_id,
            filename=attachment.filename,
            status=AttachmentProcessingStatus.SUCCESS,
            content_type=str(extracted.content_type),
        )

    def _failure(
        self,
        attachment: Attachment,
        status: str,
        error: str,
    ) -> AttachmentProcessingResult:
        self.attachment_repo.mark_processing_status(
            str(attachment.id),
            status=status,
            error=error,
        )

        if status == AttachmentProcessingStatus.UNSUPPORTED:
            logger.warning(f"Unsupported attachment {attachment.filename}: {error}")
        else:
            logger.warning(
                f"Attachment {status.lower()} for {attachment.filename}: {error}"
            )

        return AttachmentProcessingResult(
            attachment_id=str(attachment.id),
            filename=attachment.filename,
            status=status,
            error=error,
        )

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

    @staticmethod
    def _calculate_content_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def delete(self, attachment_id: str) -> None:
        self.attachment_repo.delete(attachment_id)
        self.content_repo.delete(attachment_id)
