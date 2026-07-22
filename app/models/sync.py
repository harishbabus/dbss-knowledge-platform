from pydantic import BaseModel
from typing import Optional


class SyncHistory(BaseModel):

    job_type: str

    status: str

    started_at: str

    completed_at: Optional[str] = None

    last_processed_page: Optional[str] = None

    processed_count: int = 0