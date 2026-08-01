from typing import Any

from app.config.settings import settings
from app.models.knowledge_page import KnowledgePage
from app.models.page_metadata import PageMetadata
from app.models.sync_metadata import SyncMetadata

import hashlib
from datetime import datetime, timezone


class KnowledgeBuilder:
    def _build_metadata(
        self,
        page_data: dict[str, Any],
    ) -> PageMetadata:
        history = page_data.get("history", {})

        version = page_data.get("version", {})

        return PageMetadata(
            title=page_data.get("title", ""),
            space=settings.SPACE_KEY,
            status=page_data.get("status"),
            version=version.get("number"),
            created_by=history.get("createdBy", {}).get("displayName"),
            created_date=history.get("createdDate"),
            updated_by=version.get("by", {}).get("displayName"),
            updated_date=version.get("when"),
            parent_id=(
                page_data.get("ancestors", [])[-1].get("id")
                if page_data.get("ancestors")
                else None
            ),
            ancestors=page_data.get("ancestors", []),
            labels=[
                x.get("name")
                for x in page_data.get("metadata", {})
                .get("labels", {})
                .get("results", [])
            ],
            url=page_data.get("_links", {}).get("webui", ""),
        )

    def _build_sync(
        self,
        text: str,
    ) -> SyncMetadata:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        return SyncMetadata(
            content_hash=content_hash,
            last_synced=datetime.now(timezone.utc).isoformat(),
            source="Confluence",
        )

    def build(
        self,
        page_data: dict[str, Any],
        content: dict[str, Any],
        attachments: list[dict[str, Any]],
    ) -> KnowledgePage:
        text = content.get("plain_text", "")

        return KnowledgePage(
            id=str(page_data["id"]),
            metadata=self._build_metadata(page_data),
            content=content,
            attachments=attachments,
            sync=self._build_sync(text),
        )
