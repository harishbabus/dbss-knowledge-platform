from typing import Any, Optional

from pydantic import BaseModel, Field


class PageMetadata(BaseModel):
    title: str
    space: str
    status: Optional[str] = None

    version: Optional[int] = None

    parent_id: Optional[str] = None

    created_by: Optional[str] = None
    created_date: Optional[str] = None

    updated_by: Optional[str] = None
    updated_date: Optional[str] = None

    url: str

    ancestors: list[dict[str, Any]] = Field(default_factory=list)

    labels: list[str] = Field(default_factory=list)
