from typing import List, Optional

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    #
    # Confluence Metadata
    #
    id: str

    page_id: str

    filename: str

    media_type: Optional[str] = None

    size: Optional[int] = None

    status: Optional[str] = None

    labels: List[str] = Field(default_factory=list)

    download_url: Optional[str] = None

    thumbnail_url: Optional[str] = None

    #
    # Version Information
    #
    version: Optional[int] = None

    version_when: Optional[str] = None

    version_by: Optional[str] = None

    #
    # Original Creation Information
    #
    created_by: Optional[str] = None

    created_date: Optional[str] = None

    #
    # Processing Information
    #
    content: Optional[str] = None

    content_hash: Optional[str] = None

    indexed: bool = False

    processing_status: Optional[str] = None

    processing_error: Optional[str] = None

    downloaded_path: Optional[str] = None

    last_downloaded: Optional[str] = None

    last_processed: Optional[str] = None

    #
    # Search Metadata
    #
    page_title: Optional[str] = None
