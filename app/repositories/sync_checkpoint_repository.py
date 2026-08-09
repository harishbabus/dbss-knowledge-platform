from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.storage.mongodb import mongodb


class SyncCheckpointRepository:
    """Stores the global watermark for a named synchronization job."""

    def __init__(self, collection_name: str = "sync_checkpoint") -> None:
        self.collection = mongodb.collection(collection_name)

    def get(self, sync_id: str) -> dict[str, Any] | None:
        return self.collection.find_one({"_id": sync_id})

    def get_last_successful(self, sync_id: str) -> datetime | None:
        checkpoint = self.get(sync_id)

        if not checkpoint or checkpoint.get("status") != "SUCCESS":
            return None

        value = checkpoint.get("last_sync_time")

        if isinstance(value, datetime):
            return value

        return None

    def save_success(
        self,
        sync_id: str,
        last_sync_time: datetime,
        *,
        processed_pages: int = 0,
        last_processed_page: str | None = None,
    ) -> None:
        if last_sync_time.tzinfo is None:
            last_sync_time = last_sync_time.replace(tzinfo=timezone.utc)

        self.collection.update_one(
            {"_id": sync_id},
            {
                "$set": {
                    "last_sync_time": last_sync_time,
                    "status": "SUCCESS",
                    "processed_pages": processed_pages,
                    "last_processed_page": last_processed_page,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    def save(self, checkpoint: Any) -> None:
        """Backward-compatible save for SyncCheckpoint models."""
        self.collection.update_one(
            {"_id": checkpoint.id},
            {"$set": checkpoint.model_dump()},
            upsert=True,
        )
