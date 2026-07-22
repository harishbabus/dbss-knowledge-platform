from pydantic import BaseModel
from typing import Optional


class Page(BaseModel):

    id: str

    title: str

    space: str

    url: Optional[str] = None

    parent_id: Optional[str] = None

    status: Optional[str] = None

    version: Optional[int] = None

    created_by: Optional[str] = None

    created_date: Optional[str] = None

    updated_by: Optional[str] = None

    updated_date: Optional[str] = None