from typing import Any, Dict

from pydantic import BaseModel, Field
from app.models.page_metadata import PageMetadata
from app.models.sync_metadata import SyncMetadata


class KnowledgePage(BaseModel):
    id: str

    metadata: PageMetadata

    content: Dict[str, Any] = Field(default_factory=dict)

    attachments: list[dict[str, Any]] = Field(default_factory=list)

    sync: SyncMetadata
