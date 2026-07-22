from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class PageContent(BaseModel):

    page_id: str

    raw_html: Optional[str] = None

    plain_text: Optional[str] = None

    headings: List[str] = Field(
        default_factory=list
    )

    tables: List[Dict] = Field(
        default_factory=list
    )

    code_blocks: List[Dict] = Field(
        default_factory=list
    )

    links: List[Dict] = Field(
        default_factory=list
    )

    macros: List[Dict] = Field(
        default_factory=list
    )

    content_hash: Optional[str] = None