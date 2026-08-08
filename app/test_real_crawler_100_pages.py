from time import perf_counter

from app.bootstrap.container import Container
from app.crawler.inventory import KnowledgeCrawler


def test_real_crawler_100_pages():
    container = Container()

    crawler = KnowledgeCrawler(
        page_processor=container.page_processor,
    )

    started = perf_counter()

    result = crawler.run(
        batch_size=100,
        max_pages=100,
    )

    elapsed = perf_counter() - started

    print()
    print("=" * 70)
    print("REAL 100-PAGE CRAWL")
    print("=" * 70)

    print(f"Processed : {result['processed']}")
    print(f"Saved     : {result['saved']}")
    print(f"Failed    : {result['failed']}")
    print(f"Elapsed   : {elapsed:.2f} seconds")

    #
    # Collect chunk statistics for the pages that
    # were actually processed.
    #
    processed_page_ids = {
        document["page_id"]
        for document in container.chunk_repository.collection.find(
            {},
            {"page_id": 1},
        )
    }

    total_chunks = container.chunk_repository.collection.count_documents({})

    print(f"Total chunks in MongoDB : {total_chunks}")
    print(f"Pages represented in chunks : {len(processed_page_ids)}")

    print("=" * 70)

    assert result["processed"] <= 100
    assert result["saved"] + result["failed"] == result["processed"]

    #
    # We expect Confluence to return the requested
    # 100 pages unless fewer pages are available.
    #
    assert result["processed"] > 0
