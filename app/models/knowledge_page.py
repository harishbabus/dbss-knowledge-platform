from typing import Dict, List

from pydantic import BaseModel, Field


class KnowledgePage(BaseModel):

    id: str

    metadata: Dict = Field(default_factory=dict)

    content: Dict = Field(default_factory=dict)

    attachments: List[Dict] = Field(default_factory=list)

    sync: Dict = Field(default_factory=dict)
