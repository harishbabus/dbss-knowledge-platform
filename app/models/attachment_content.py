from pydantic import BaseModel
from typing import Optional


class AttachmentContent(BaseModel):

    id: str

    page_id: str

    filename: str

    content_type: Optional[str] = None

    text: Optional[str] = None

    file_path: Optional[str] = None

    content_hash: Optional[str] = None
