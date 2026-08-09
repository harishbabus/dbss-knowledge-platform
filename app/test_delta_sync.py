from datetime import datetime, timezone

import pytest
from unittest.mock import MagicMock

from app.crawler.delta_sync import DeltaSyncCrawler


def _crawler():
    crawler = DeltaSyncCrawler.__new__(DeltaSyncCrawler)
    crawler.client = MagicMock()
    crawler.page_processor = MagicMock()
    crawler.sync_state_repository = MagicMock()
    crawler.checkpoint_repository = MagicMock()
    crawler.sync_id = "DPCC:confluence_delta"
    return crawler


def test_delta_processes_new_page():
    crawler = _crawler()

    crawler.client.get_pages_modified_after.return_value = {"results": [{"id": "123"}]}
    crawler.client.get_page_details.return_value = {
        "id": "123",
        "version": {"number": 5, "when": "2026-08-09T01:00:00Z"},
    }
    crawler.sync_state_repository.get.return_value = None

    result = crawler.run("2026-08-09 00:00")

    assert result == {
        "candidates": 1,
        "processed": 1,
        "skipped": 0,
        "saved": 1,
        "failed": 0,
    }
    crawler.page_processor.process.assert_called_once()
    crawler.checkpoint_repository.save_success.assert_called_once()


def test_delta_skips_same_version():
    crawler = _crawler()

    crawler.client.get_pages_modified_after.return_value = {"results": [{"id": "123"}]}
    crawler.client.get_page_details.return_value = {
        "id": "123",
        "version": {"number": 5, "when": "2026-08-09T01:00:00Z"},
    }
    crawler.sync_state_repository.get.return_value = {
        "page_id": "123",
        "version": 5,
    }

    result = crawler.run("2026-08-09 00:00")

    assert result["processed"] == 0
    assert result["skipped"] == 1
    assert result["failed"] == 0
    crawler.page_processor.process.assert_not_called()
    crawler.checkpoint_repository.save_success.assert_called_once()


def test_delta_processes_changed_version():
    crawler = _crawler()

    crawler.client.get_pages_modified_after.return_value = {"results": [{"id": "123"}]}
    crawler.client.get_page_details.return_value = {
        "id": "123",
        "version": {"number": 6, "when": "2026-08-09T02:00:00Z"},
    }
    crawler.sync_state_repository.get.return_value = {
        "page_id": "123",
        "version": 5,
    }

    result = crawler.run("2026-08-09 00:00")

    assert result["processed"] == 1
    assert result["skipped"] == 0
    assert result["failed"] == 0
    crawler.page_processor.process.assert_called_once()
    crawler.sync_state_repository.save.assert_called_once()
    crawler.checkpoint_repository.save_success.assert_called_once()


def test_delta_processes_multiple_batches():
    crawler = _crawler()

    crawler.client.get_pages_modified_after.side_effect = [
        {"results": [{"id": "1"}, {"id": "2"}]},
        {"results": [{"id": "3"}]},
        {"results": []},
    ]

    crawler.client.get_page_details.side_effect = lambda page_id: {
        "id": page_id,
        "version": {"number": 1, "when": "2026-01-01T00:00:00Z"},
    }

    crawler.sync_state_repository.get.return_value = None

    result = crawler.run(
        modified_after="2026-01-01 00:00",
        batch_size=2,
    )

    assert result["candidates"] == 3
    assert result["processed"] == 3
    assert result["skipped"] == 0
    assert result["saved"] == 3
    assert result["failed"] == 0

    assert crawler.client.get_pages_modified_after.call_count == 2

    calls = crawler.client.get_pages_modified_after.call_args_list
    assert calls[0].kwargs["start"] == 0
    assert calls[0].kwargs["limit"] == 2
    assert calls[1].kwargs["start"] == 2
    assert calls[1].kwargs["limit"] == 2

    crawler.checkpoint_repository.save_success.assert_called_once()


def test_delta_rejects_invalid_batch_size():
    crawler = _crawler()

    with pytest.raises(ValueError):
        crawler.run(
            modified_after="2026-01-01 00:00",
            batch_size=0,
        )


def test_delta_uses_checkpoint_when_modified_after_is_omitted():
    crawler = _crawler()

    checkpoint = datetime(2026, 8, 9, 12, 30, tzinfo=timezone.utc)
    crawler.checkpoint_repository.get_last_successful.return_value = checkpoint
    crawler.client.get_pages_modified_after.return_value = {"results": []}

    result = crawler.run()

    assert result["candidates"] == 0
    crawler.client.get_pages_modified_after.assert_called_once_with(
        "2026-08-09 12:30",
        start=0,
        limit=100,
    )
    crawler.checkpoint_repository.save_success.assert_called_once()


def test_delta_requires_checkpoint_when_modified_after_is_omitted():
    crawler = _crawler()
    crawler.checkpoint_repository.get_last_successful.return_value = None

    with pytest.raises(ValueError, match="No successful sync checkpoint"):
        crawler.run()


def test_delta_does_not_advance_checkpoint_when_page_fails():
    crawler = _crawler()

    crawler.client.get_pages_modified_after.return_value = {"results": [{"id": "123"}]}
    crawler.client.get_page_details.return_value = {
        "id": "123",
        "version": {"number": 5, "when": "2026-08-09T01:00:00Z"},
    }
    crawler.sync_state_repository.get.return_value = None
    crawler.page_processor.process.side_effect = RuntimeError("processing failed")

    result = crawler.run("2026-08-09 00:00")

    assert result["processed"] == 0
    assert result["failed"] == 1
    crawler.checkpoint_repository.save_success.assert_not_called()
