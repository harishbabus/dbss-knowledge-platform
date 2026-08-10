from unittest.mock import MagicMock

from app.connectors.attachment_downloader import DownloadResult
from app.models.attachment import Attachment
from app.models.content_type import ContentType
from app.models.extracted_content import ExtractedContent
from app.models.attachment_processing_result import AttachmentProcessingStatus
from app.services.attachment_processor import AttachmentProcessor


def _attachment(filename="test.txt"):
    return Attachment(
        id="att-1",
        page_id="page-1",
        filename=filename,
        media_type="text/plain",
        size=4,
        version=1,
        download_url="https://example.com/test.txt",
    )


def _processor(tmp_path):
    path = tmp_path / "page-1" / "att-1_test.txt"
    path.parent.mkdir(parents=True)
    path.write_text("hello", encoding="utf-8")
    downloader = MagicMock()
    downloader.download_with_metadata.return_value = DownloadResult(
        path, "binary-hash", 5
    )
    extractor = MagicMock()
    extractor.extract_with_status.return_value = (
        AttachmentProcessingStatus.SUCCESS,
        ExtractedContent(
            text="hello",
            content_type=ContentType.TEXT,
            file_path=str(path),
            metadata={},
        ),
        None,
    )
    return AttachmentProcessor(MagicMock(), MagicMock(), downloader, extractor)


def test_process_success(tmp_path):
    processor = _processor(tmp_path)
    result = processor.process(_attachment(), "page-1")
    assert result.succeeded
    assert result.status == AttachmentProcessingStatus.SUCCESS
    processor.content_repo.save.assert_called_once()
    processor.attachment_repo.mark_indexed.assert_called_once()


def test_process_download_failure(tmp_path):
    processor = _processor(tmp_path)
    processor.downloader.download_with_metadata.return_value = None
    result = processor.process(_attachment(), "page-1")
    assert result.status == AttachmentProcessingStatus.DOWNLOAD_FAILED
    processor.content_repo.save.assert_not_called()


def test_process_unsupported(tmp_path):
    processor = _processor(tmp_path)
    processor.content_extractor.extract_with_status.return_value = (
        AttachmentProcessingStatus.UNSUPPORTED,
        None,
        "No extractor",
    )
    result = processor.process(_attachment(), "page-1")
    assert result.status == AttachmentProcessingStatus.UNSUPPORTED
    processor.attachment_repo.mark_processing_status.assert_called_once()
