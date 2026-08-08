from app.bootstrap.container import Container
from app.crawler.inventory import KnowledgeCrawler


PAGE_ID = "150710119"


def test_real_crawler_single_page():
    container = Container()

    crawler = KnowledgeCrawler(
        page_processor=container.page_processor,
    )

    #
    # Keep the crawler's real processing logic,
    # but control pagination so only one known
    # real Confluence page is processed.
    #
    original_get_pages = crawler.client.get_pages

    calls = 0

    def get_one_page(*, start: int = 0, limit: int = 100):
        nonlocal calls

        if calls == 0:
            calls += 1

            return {
                "results": [
                    {
                        "id": PAGE_ID,
                    }
                ]
            }

        return {"results": []}

    crawler.client.get_pages = get_one_page

    try:
        result = crawler.run(batch_size=1)
    finally:
        crawler.client.get_pages = original_get_pages

    #
    # Verify crawler result.
    #
    assert result["processed"] == 1
    assert result["saved"] == 1
    assert result["failed"] == 0

    #
    # Verify chunks persisted by the actual
    # PageProcessor → IndexingPipeline.
    #
    chunks = list(container.chunk_repository.collection.find({"page_id": PAGE_ID}))

    assert len(chunks) == 11

    assert len({chunk.get("id") for chunk in chunks}) == 11

    assert all(chunk.get("splitter") == "hierarchical" for chunk in chunks)

    assert all(len(chunk.get("text", "")) <= 1200 for chunk in chunks)
