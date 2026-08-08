from datetime import datetime, timezone

from app.models.knowledge_chunk import KnowledgeChunk
from app.storage.mongodb import mongodb


class KnowledgeChunkRepository:
    def __init__(
        self,
        collection_name: str = "knowledge_chunks",
    ):
        self.collection = mongodb.collection(collection_name)

    def save(
        self,
        chunk: KnowledgeChunk,
    ) -> None:
        document = chunk.model_dump()

        document["updated_at"] = datetime.now(timezone.utc)

        self.collection.update_one(
            {"id": chunk.id},
            {"$set": document},
            upsert=True,
        )

    def save_many(
        self,
        chunks: list[KnowledgeChunk],
    ) -> None:
        for chunk in chunks:
            self.save(chunk)

    def count(
        self,
    ) -> int:
        return self.collection.count_documents({})

    def replace_for_page(
        self,
        page_id: str,
        chunks: list[KnowledgeChunk],
    ) -> None:
        self.collection.delete_many({"page_id": page_id})

        if chunks:
            self.save_many(chunks)
