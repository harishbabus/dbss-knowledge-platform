from app.bootstrap.container import Container
from app.connectors.confluence_client import ConfluenceClient


def test_real_confluence_page_through_pipeline():
    page_id = "150710119"

    container = Container()

    client = ConfluenceClient()

    page_data = client.get_page_details(page_id)

    knowledge_page = container.page_processor.process(
        page_id,
        page_data,
    )

    assert knowledge_page is not None

    print()
    print("=" * 70)
    print("REAL PAGE PIPELINE VALIDATION")
    print("=" * 70)

    print(f"Page ID : {page_id}")

    print(f"Title   : {knowledge_page.metadata.title}")

    chunks = container.chunk_repository.collection.find({"page_id": page_id})

    chunks = list(chunks)

    print(f"Chunks  : {len(chunks)}")

    for chunk in sorted(
        chunks,
        key=lambda item: item.get("sequence", 0),
    ):
        text = chunk.get("text", "")

        print()
        print(f"Chunk {chunk.get('sequence')}")

        print(f"Splitter : {chunk.get('splitter')}")

        print(f"Length   : {len(text)}")

        print(f"Preview  : {text[:150]!r}")

    assert len(chunks) == 11

    assert len({chunk.get("id") for chunk in chunks}) == 11

    assert all(chunk.get("splitter") == "hierarchical" for chunk in chunks)

    assert all(len(chunk.get("text", "")) <= 1200 for chunk in chunks)
