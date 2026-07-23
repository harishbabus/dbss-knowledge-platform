from app.models.knowledge_page import KnowledgePage
from app.extractors.attachment_extractor import AttachmentExtractor
from app.storage.attachment_repository import AttachmentRepository

import hashlib
from datetime import datetime, timezone


class KnowledgeBuilder:

    def __init__(self):

        self.attachment_extractor = AttachmentExtractor()

        self.attachment_repository = AttachmentRepository()

    def build(self, page_data: dict, content: dict, attachments: list):

        text = content.get("plain_text", "")

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        metadata = {
            "title": page_data.get("title"),
            "space": "DPCC",
            "status": page_data.get("status"),
            "version": page_data.get("version", {}).get("number"),
            "created_by": page_data.get("history", {})
            .get("createdBy", {})
            .get("displayName"),
            "created_date": page_data.get("history", {}).get("createdDate"),
            "updated_by": page_data.get("version", {}).get("by", {}).get("displayName"),
            "updated_date": page_data.get("version", {}).get("when"),
            "parent_id": (
                page_data.get("ancestors", [])[-1].get("id")
                if page_data.get("ancestors")
                else None
            ),
            "ancestors": page_data.get("ancestors", []),
            "labels": [
                x.get("name")
                for x in page_data.get("metadata", {})
                .get("labels", {})
                .get("results", [])
            ],
        }

        sync = {
            "content_hash": content_hash,
            "last_synced": datetime.now(timezone.utc).isoformat(),
            "source": "Confluence",
        }

        return KnowledgePage(
            id=str(page_data["id"]),
            metadata=metadata,
            content=content,
            attachments=attachments,
            sync=sync,
        )
