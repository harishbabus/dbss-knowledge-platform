from app.bootstrap.container import Container
from app.crawler.inventory import KnowledgeCrawler


PAGE_IDS = [
    "127489206",
    "69470791",
    "52082748",
    "150725254",
    "91298023",
    "171000541",
    "138719399",
    "52080535",
    "52080562",
    "52080563",
]

EXPECTED_CHUNK_COUNTS = {
    "127489206": 29,
    "69470791": 1,
    "52082748": 8,
    "150725254": 1,
    "91298023": 4,
    "171000541": 12,
    "138719399": 3,
    "52080535": 0,
    "52080562": 1,
    "52080563": 1,
}


def _get_chunk_counts(
    container: Container,
) -> dict[str, int]:
    return {
        page_id: container.chunk_repository.collection.count_documents(
            {"page_id": page_id}
        )
        for page_id in PAGE_IDS
    }


def test_real_crawler_is_idempotent():
    container = Container()

    crawler = KnowledgeCrawler(
        page_processor=container.page_processor,
    )

    original_get_pages = crawler.client.get_pages

    calls = 0

    def get_ten_pages(
        *,
        start: int = 0,
        limit: int = 100,
    ):
        nonlocal calls

        if calls == 0:
            calls += 1

            return {"results": [{"id": page_id} for page_id in PAGE_IDS]}

        return {"results": []}

    crawler.client.get_pages = get_ten_pages

    try:
        print()
        print("=" * 70)
        print("FIRST CRAWL")
        print("=" * 70)

        first_result = crawler.run(
            batch_size=10,
        )

        assert first_result["processed"] == 10
        assert first_result["saved"] == 10
        assert first_result["failed"] == 0

        first_counts = _get_chunk_counts(
            container,
        )

        print()
        print("First-run chunk counts:")

        for page_id, count in first_counts.items():
            print(f"Page {page_id}: {count} chunks")

        #
        # Reset the controlled pagination.
        #
        calls = 0

        print()
        print("=" * 70)
        print("SECOND CRAWL")
        print("=" * 70)

        second_result = crawler.run(
            batch_size=10,
        )

        assert second_result["processed"] == 10
        assert second_result["saved"] == 10
        assert second_result["failed"] == 0

        second_counts = _get_chunk_counts(
            container,
        )

        print()
        print("Second-run chunk counts:")

        for page_id, count in second_counts.items():
            print(f"Page {page_id}: {count} chunks")

        #
        # The second crawl must produce exactly
        # the same number of chunks.
        #
        assert second_counts == first_counts

        #
        # Also verify the known expected counts.
        #
        assert second_counts == EXPECTED_CHUNK_COUNTS

        #
        # Verify there are no duplicate chunk IDs.
        #
        for page_id in PAGE_IDS:
            chunks = list(
                container.chunk_repository.collection.find({"page_id": page_id})
            )

            chunk_ids = [chunk["id"] for chunk in chunks]

            assert len(chunk_ids) == len(set(chunk_ids))

    finally:
        crawler.client.get_pages = original_get_pages

    print()
    print("=" * 70)
    print("IDEMPOTENCY VALIDATION PASSED")
    print("=" * 70)

    print(f"Total chunks after second crawl: {sum(second_counts.values())}")
