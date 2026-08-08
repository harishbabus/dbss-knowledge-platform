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
EXPECTED_EMPTY_PAGES = {
    "52080535",
}


def test_real_crawler_ten_pages():
    container = Container()

    crawler = KnowledgeCrawler(
        page_processor=container.page_processor,
    )

    original_get_pages = crawler.client.get_pages

    calls = 0

    def get_ten_pages(*, start: int = 0, limit: int = 100):
        nonlocal calls

        if calls == 0:
            calls += 1

            return {"results": [{"id": page_id} for page_id in PAGE_IDS]}

        return {"results": []}

    crawler.client.get_pages = get_ten_pages

    try:
        result = crawler.run(batch_size=10)
    finally:
        crawler.client.get_pages = original_get_pages

    print()
    print("=" * 70)
    print("REAL 10-PAGE CRAWLER VALIDATION")
    print("=" * 70)

    print(f"Processed : {result['processed']}")
    print(f"Saved     : {result['saved']}")
    print(f"Failed    : {result['failed']}")

    assert result["processed"] == 10
    assert result["saved"] == 10
    assert result["failed"] == 0

    total_chunks = 0

    for page_id in PAGE_IDS:
        chunks = list(container.chunk_repository.collection.find({"page_id": page_id}))

        print()
        print(f"Page {page_id}: {len(chunks)} chunks")

        if page_id in EXPECTED_EMPTY_PAGES:
            assert len(chunks) == 0
            continue

        assert len(chunks) > 0

        assert len({chunk.get("id") for chunk in chunks}) == len(chunks)

        assert all(chunk.get("splitter") == "hierarchical" for chunk in chunks)

        assert all(len(chunk.get("text", "")) <= 1200 for chunk in chunks)

        total_chunks += len(chunks)

    print()
    print(f"Total chunks generated: {total_chunks}")
