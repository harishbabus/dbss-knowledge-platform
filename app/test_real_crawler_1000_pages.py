from time import perf_counter

from app.bootstrap.container import Container
from app.crawler.inventory import KnowledgeCrawler


def test_real_crawler_1000_pages():
    container = Container()

    crawler = KnowledgeCrawler(
        page_processor=container.page_processor,
    )

    #
    # Capture the exact page IDs that this run is expected
    # to process. This lets the statistics below ignore
    # chunks left by earlier integration tests.
    #
    expected_page_ids: list[str] = []

    start = 0

    while len(expected_page_ids) < 1000:
        response = crawler.client.get_pages(
            start=start,
            limit=100,
        )

        pages = response.get("results", [])

        if not pages:
            break

        remaining = 1000 - len(expected_page_ids)

        expected_page_ids.extend(page["id"] for page in pages[:remaining])

        start += len(pages)

    assert len(expected_page_ids) == 1000

    assert expected_page_ids

    started = perf_counter()

    result = crawler.run(
        batch_size=100,
        max_pages=1000,
    )

    elapsed = perf_counter() - started

    #
    # Calculate statistics only for the pages belonging
    # to this 1000-page run.
    #
    page_chunk_counts = {
        page_id: container.chunk_repository.collection.count_documents(
            {"page_id": page_id}
        )
        for page_id in expected_page_ids
    }

    total_chunks = sum(page_chunk_counts.values())

    pages_with_chunks = sum(count > 0 for count in page_chunk_counts.values())

    pages_without_chunks = sum(count == 0 for count in page_chunk_counts.values())

    non_zero_counts = [count for count in page_chunk_counts.values() if count > 0]

    average_chunks = total_chunks / len(expected_page_ids) if expected_page_ids else 0.0

    pages_per_second = result["processed"] / elapsed if elapsed > 0 else 0.0

    print()
    print("=" * 70)
    print("REAL 1000-PAGE CRAWL")
    print("=" * 70)

    print(f"Processed           : {result['processed']}")
    print(f"Saved               : {result['saved']}")
    print(f"Failed              : {result['failed']}")
    print(f"Elapsed             : {elapsed:.2f} seconds")
    print(f"Pages / second      : {pages_per_second:.2f}")
    print(f"Pages with chunks   : {pages_with_chunks}")
    print(f"Pages without chunks: {pages_without_chunks}")
    print(f"Total chunks        : {total_chunks}")
    print(f"Average chunks/page : {average_chunks:.2f}")

    if non_zero_counts:
        print(f"Minimum chunks/page : {min(non_zero_counts)}")
        print(f"Maximum chunks/page : {max(non_zero_counts)}")
    else:
        print("Minimum chunks/page : 0")
        print("Maximum chunks/page : 0")

    print("=" * 70)

    assert result["processed"] <= 1000
    assert result["saved"] + result["failed"] == result["processed"]
    assert result["processed"] == len(expected_page_ids)
    assert result["failed"] == 0
