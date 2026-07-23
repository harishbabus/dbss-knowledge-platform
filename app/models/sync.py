from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SyncHistory(BaseModel):

    job_type: str

    status: str

    started_at: datetime

    completed_at: Optional[datetime] = None

    processed_count: int = 0

    failed_count: int = 0

    last_processed_page: Optional[str] = None

    error_message: Optional[str] = None