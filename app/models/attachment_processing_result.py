from __future__ import annotations

from dataclasses import dataclass


class AttachmentProcessingStatus:
    SUCCESS = "SUCCESS"
    UNSUPPORTED = "UNSUPPORTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"


@dataclass(frozen=True)
class AttachmentProcessingResult:
    attachment_id: str
    filename: str
    status: str
    error: str | None = None
    content_type: str | None = None

    def __bool__(self) -> bool:
        return self.status == AttachmentProcessingStatus.SUCCESS

    @property
    def succeeded(self) -> bool:
        return self.status == AttachmentProcessingStatus.SUCCESS
