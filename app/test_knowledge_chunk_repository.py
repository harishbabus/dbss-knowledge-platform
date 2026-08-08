from datetime import datetime, timezone

from app.models.knowledge_chunk import KnowledgeChunk
from app.storage.knowledge_chunk_repository import (
    KnowledgeChunkRepository,
)


TEST_COLLECTION = "knowledge_chunks_test"


def _create_chunk(
    page_id: str,
    sequence: int,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=f"{page_id}_{sequence:04d}",
        page_id=page_id,
        sequence=sequence,
        title="Test Page",
        text=f"Test chunk {sequence}",
        splitter="heading",
        metadata={
            "space": "DPCC",
            "labels": [],
        },
        token_count=0,
        embedding_model=None,
        embedding_version=1,
        created_at=datetime.now(timezone.utc),
    )


def test_replace_for_page_removes_obsolete_chunks():
    repository = KnowledgeChunkRepository(
        collection_name=TEST_COLLECTION,
    )

    page_id = "test-replace-page"

    try:
        #
        # Start clean
        #
        repository.collection.delete_many({"page_id": page_id})

        #
        # Initial version: 5 chunks
        #
        initial_chunks = [_create_chunk(page_id, sequence) for sequence in range(1, 6)]

        repository.save_many(initial_chunks)

        assert repository.collection.count_documents({"page_id": page_id}) == 5

        #
        # Updated version: only 3 chunks
        #
        updated_chunks = [_create_chunk(page_id, sequence) for sequence in range(1, 4)]

        repository.replace_for_page(
            page_id,
            updated_chunks,
        )

        #
        # Verify obsolete chunks are gone
        #
        assert repository.collection.count_documents({"page_id": page_id}) == 3

        stored_ids = {
            document["id"]
            for document in repository.collection.find(
                {"page_id": page_id},
                {"id": 1},
            )
        }

        assert stored_ids == {
            "test-replace-page_0001",
            "test-replace-page_0002",
            "test-replace-page_0003",
        }

    finally:
        #
        # Always clean up test data
        #
        repository.collection.delete_many({"page_id": page_id})


def test_replace_for_page_with_empty_chunks_deletes_all():
    repository = KnowledgeChunkRepository(
        collection_name=TEST_COLLECTION,
    )

    page_id = "test-empty-page"

    try:
        #
        # Create existing chunks
        #
        chunks = [_create_chunk(page_id, sequence) for sequence in range(1, 4)]

        repository.save_many(chunks)

        assert repository.collection.count_documents({"page_id": page_id}) == 3

        #
        # Replace with no chunks
        #
        repository.replace_for_page(
            page_id,
            [],
        )

        #
        # All previous chunks must disappear
        #
        assert repository.collection.count_documents({"page_id": page_id}) == 0

    finally:
        repository.collection.delete_many({"page_id": page_id})
