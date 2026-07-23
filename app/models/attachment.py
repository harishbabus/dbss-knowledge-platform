from pydantic import BaseModel
from typing import Optional, List


class Attachment(BaseModel):

    id: str

    page_id: str

    filename: str

    media_type: Optional[str] = None

    size: Optional[int] = None

    download_url: Optional[str] = None

    thumbnail_url: Optional[str] = None

    status: Optional[str] = None

    labels: List[str] = []

    created_by: Optional[str] = None

    created_date: Optional[str] = None

    version: Optional[int] = None

    content: Optional[str] = None

    content_hash: Optional[str] = None

    page_title: Optional[str] = None

    indexed: bool = False
