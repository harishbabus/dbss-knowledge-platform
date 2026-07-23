from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SyncCheckpoint(BaseModel):

    id: str

    last_sync_time: datetime

    status: str

    processed_pages: int = 0

    last_processed_page: Optional[str] = None