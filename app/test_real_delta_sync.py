from datetime import datetime, timedelta, timezone

from app.bootstrap.container import Container
from app.connectors.confluence_client import ConfluenceClient
from app.crawler.delta_sync import DeltaSyncCrawler
from app.storage.page_sync_state_repository import PageSyncStateRepository


PAGE_ID = "150710119"


def _get_chunks(container: Container) -> list[dict]:
    return list(container.chunk_repository.collection.find({"page_id": PAGE_ID}))


def test_real_delta_sync_skips_unchanged_page():
    container = Container()
    client = ConfluenceClient()

    sync_state_repository = PageSyncStateRepository()

    #
    # Fetch the real page from Confluence.
    #
    page = client.get_page_details(PAGE_ID)

    assert page["id"] == PAGE_ID

    version = page.get("version", {}).get("number")
    modified_at = page.get("version", {}).get("when")

    assert version is not None
    assert modified_at

    #
    # Process the real page normally.
    #
    container.page_processor.process(
        PAGE_ID,
        page,
    )

    #
    # Establish the current sync state.
    #
    sync_state_repository.save(
        page_id=PAGE_ID,
        version=version,
        modified_at=modified_at,
    )

    original_chunks = _get_chunks(container)

    assert original_chunks

    #
    # Create a valid timestamp string for the delta crawler.
    #
    modified_datetime = datetime.fromisoformat(modified_at.replace("Z", "+00:00"))

    modified_after = (
        (modified_datetime - timedelta(minutes=1))
        .astimezone(timezone.utc)
        .strftime("%Y-%m-%d %H:%M")
    )

    #
    # Create the real delta crawler.
    #
    crawler = DeltaSyncCrawler(
        page_processor=container.page_processor,
        sync_state_repository=sync_state_repository,
    )

    #
    # IMPORTANT:
    #
    # We do NOT want this test to retrieve 100 unrelated
    # Confluence pages that happen to have been modified
    # around the same time.
    #
    # We only want to test the delta-sync decision for our
    # known real page.
    #
    # The actual page details are STILL fetched from real
    # Confluence by DeltaSyncCrawler.
    #
    original_get_pages_modified_after = crawler.client.get_pages_modified_after

    def get_target_page_only(
        modified_after,
        *,
        start=0,
        limit=100,
    ):
        return {
            "results": [
                {
                    "id": PAGE_ID,
                }
            ]
        }

    crawler.client.get_pages_modified_after = get_target_page_only

    try:
        #
        # Run delta synchronization.
        #
        result = crawler.run(
            modified_after=modified_after,
        )
    finally:
        #
        # Restore the real method.
        #
        crawler.client.get_pages_modified_after = original_get_pages_modified_after

    #
    # Print useful integration-test information.
    #
    print()
    print("=" * 70)
    print("REAL DELTA SYNC - UNCHANGED PAGE")
    print("=" * 70)
    print(f"Page ID        : {PAGE_ID}")
    print(f"Current version: {version}")
    print(f"Modified after : {modified_after}")
    print(f"Candidates     : {result['candidates']}")
    print(f"Processed      : {result['processed']}")
    print(f"Skipped        : {result['skipped']}")
    print(f"Saved          : {result['saved']}")
    print(f"Failed         : {result['failed']}")
    print("=" * 70)

    #
    # Verify the page was discovered.
    #
    assert result["candidates"] == 1

    #
    # Because the current version is already stored,
    # the page must be skipped.
    #
    assert result["processed"] == 0
    assert result["skipped"] == 1
    assert result["saved"] == 0
    assert result["failed"] == 0

    #
    # Verify that the existing chunks were not removed
    # or replaced.
    #
    final_chunks = _get_chunks(container)

    assert len(final_chunks) == len(original_chunks)

    original_chunk_ids = {chunk["id"] for chunk in original_chunks}

    final_chunk_ids = {chunk["id"] for chunk in final_chunks}

    assert final_chunk_ids == original_chunk_ids


def test_real_delta_sync_processes_changed_page():
    container = Container()
    client = ConfluenceClient()

    sync_state_repository = PageSyncStateRepository()

    #
    # Fetch the real page from Confluence.
    #
    page = client.get_page_details(PAGE_ID)

    assert page["id"] == PAGE_ID

    version = page.get("version", {}).get("number")
    modified_at = page.get("version", {}).get("when")

    assert version is not None
    assert modified_at

    #
    # Process the page normally so that we have
    # an existing set of chunks.
    #
    container.page_processor.process(
        PAGE_ID,
        page,
    )

    original_chunks = _get_chunks(container)

    assert original_chunks

    #
    # Establish an intentionally OLD sync state.
    #
    # This simulates the situation where the page has
    # changed in Confluence since the last synchronization.
    #
    old_version = max(0, int(version) - 1)

    sync_state_repository.save(
        page_id=PAGE_ID,
        version=old_version,
        modified_at=modified_at,
    )

    #
    # Create a valid delta timestamp.
    #
    modified_datetime = datetime.fromisoformat(modified_at.replace("Z", "+00:00"))

    modified_after = (
        (modified_datetime - timedelta(minutes=1))
        .astimezone(timezone.utc)
        .strftime("%Y-%m-%d %H:%M")
    )

    #
    # Create the real delta crawler.
    #
    crawler = DeltaSyncCrawler(
        page_processor=container.page_processor,
        sync_state_repository=sync_state_repository,
    )

    #
    # Control only the candidate list.
    #
    # The actual page details will still be fetched from
    # real Confluence by DeltaSyncCrawler.
    #
    original_get_pages_modified_after = crawler.client.get_pages_modified_after

    def get_target_page_only(modified_after, *, start=0, limit=100):
        return {
            "results": [
                {
                    "id": PAGE_ID,
                }
            ]
        }

    crawler.client.get_pages_modified_after = get_target_page_only

    try:
        #
        # Run delta synchronization.
        #
        result = crawler.run(
            modified_after=modified_after,
        )
    finally:
        #
        # Restore the real method.
        #
        crawler.client.get_pages_modified_after = original_get_pages_modified_after

    #
    # Print useful integration-test information.
    #
    print()
    print("=" * 70)
    print("REAL DELTA SYNC - CHANGED PAGE")
    print("=" * 70)
    print(f"Page ID        : {PAGE_ID}")
    print(f"Stored version : {old_version}")
    print(f"Current version: {version}")
    print(f"Modified after : {modified_after}")
    print(f"Candidates     : {result['candidates']}")
    print(f"Processed      : {result['processed']}")
    print(f"Skipped        : {result['skipped']}")
    print(f"Saved          : {result['saved']}")
    print(f"Failed         : {result['failed']}")
    print("=" * 70)

    #
    # The page was discovered.
    #
    assert result["candidates"] == 1

    #
    # The stored version is older than the real page version,
    # therefore the page must be processed.
    #
    assert result["processed"] == 1
    assert result["skipped"] == 0
    assert result["saved"] == 1
    assert result["failed"] == 0

    #
    # Verify that chunks still exist after reprocessing.
    #
    final_chunks = _get_chunks(container)

    assert final_chunks

    #
    # The replacement should result in a valid set of
    # unique chunk IDs.
    #
    final_chunk_ids = {chunk["id"] for chunk in final_chunks}

    assert len(final_chunk_ids) == len(final_chunks)

    #
    # Verify the stored sync state now contains the
    # current Confluence version.
    #
    saved_state = sync_state_repository.get(PAGE_ID)

    assert saved_state is not None
    assert saved_state["version"] == version
    assert saved_state["modified_at"] == modified_at


def test_real_delta_sync_processes_new_page():
    container = Container()
    client = ConfluenceClient()

    sync_state_repository = PageSyncStateRepository()

    #
    # Fetch the real page from Confluence.
    #
    page = client.get_page_details(PAGE_ID)

    assert page["id"] == PAGE_ID

    version = page.get("version", {}).get("number")
    modified_at = page.get("version", {}).get("when")

    assert version is not None
    assert modified_at

    #
    # Make sure this page is NOT already present in the
    # sync-state repository.
    #
    sync_state_repository.collection.delete_one({"page_id": PAGE_ID})

    assert sync_state_repository.get(PAGE_ID) is None

    #
    # Create a valid delta timestamp.
    #
    modified_datetime = datetime.fromisoformat(modified_at.replace("Z", "+00:00"))

    modified_after = (
        (modified_datetime - timedelta(minutes=1))
        .astimezone(timezone.utc)
        .strftime("%Y-%m-%d %H:%M")
    )

    #
    # Create the real delta crawler.
    #
    crawler = DeltaSyncCrawler(
        page_processor=container.page_processor,
        sync_state_repository=sync_state_repository,
    )

    #
    # Control only the candidate list.
    #
    # The page details are still retrieved from real
    # Confluence by DeltaSyncCrawler.
    #
    original_get_pages_modified_after = crawler.client.get_pages_modified_after

    def get_target_page_only(
        modified_after,
        *,
        start=0,
        limit=100,
    ):
        return {
            "results": [
                {
                    "id": PAGE_ID,
                }
            ]
        }

    crawler.client.get_pages_modified_after = get_target_page_only

    try:
        #
        # Run delta synchronization.
        #
        result = crawler.run(
            modified_after=modified_after,
        )
    finally:
        #
        # Restore the real method.
        #
        crawler.client.get_pages_modified_after = original_get_pages_modified_after

    #
    # Print useful integration-test information.
    #
    print()
    print("=" * 70)
    print("REAL DELTA SYNC - NEW PAGE")
    print("=" * 70)
    print(f"Page ID        : {PAGE_ID}")
    print(f"Current version: {version}")
    print(f"Modified after : {modified_after}")
    print(f"Candidates     : {result['candidates']}")
    print(f"Processed      : {result['processed']}")
    print(f"Skipped        : {result['skipped']}")
    print(f"Saved          : {result['saved']}")
    print(f"Failed         : {result['failed']}")
    print("=" * 70)

    #
    # The page should have been discovered.
    #
    assert result["candidates"] == 1

    #
    # Because there is no existing sync state,
    # this is a new page from the delta-sync perspective.
    #
    assert result["processed"] == 1
    assert result["skipped"] == 0
    assert result["saved"] == 1
    assert result["failed"] == 0

    #
    # Verify that chunks were actually generated.
    #
    chunks = _get_chunks(container)

    assert chunks

    #
    # Verify chunk IDs are unique.
    #
    chunk_ids = {chunk["id"] for chunk in chunks}

    assert len(chunk_ids) == len(chunks)

    #
    # Verify that sync state was created.
    #
    saved_state = sync_state_repository.get(PAGE_ID)

    assert saved_state is not None
    assert saved_state["version"] == version
    assert saved_state["modified_at"] == modified_at
