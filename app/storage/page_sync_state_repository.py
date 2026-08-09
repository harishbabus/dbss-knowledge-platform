from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.storage.mongodb import mongodb


class PageSyncStateRepository:
    """Stores the last successfully indexed Confluence state for each page."""

    def __init__(self, collection_name: str = "page_sync_state") -> None:
        self.collection = mongodb.collection(collection_name)

    def get(self, page_id: str) -> dict[str, Any] | None:
        return self.collection.find_one({"page_id": str(page_id)})

    def save(
        self,
        page_id: str,
        version: int | None,
        modified_at: str | None,
    ) -> None:
        self.collection.update_one(
            {"page_id": str(page_id)},
            {
                "$set": {
                    "page_id": str(page_id),
                    "version": version,
                    "modified_at": modified_at,
                    "synced_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    def delete(self, page_id: str) -> None:
        self.collection.delete_one({"page_id": str(page_id)})
