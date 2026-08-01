from typing import Any
from pydantic import BaseModel, Field
from app.models.content_type import ContentType


class ExtractedContent(BaseModel):
    text: str
    content_type: ContentType
    file_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
