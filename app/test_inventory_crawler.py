from unittest.mock import MagicMock

import pytest

from app.crawler.inventory import KnowledgeCrawler


def test_run_respects_max_pages():
    crawler = KnowledgeCrawler.__new__(KnowledgeCrawler)

    crawler.client = MagicMock()
    crawler.page_processor = MagicMock()
    crawler.checkpoint_repository = MagicMock()
    crawler.sync_id = "DPCC:confluence_delta"

    crawler.client.get_pages.side_effect = [
        {
            "results": [
                {"id": "1"},
                {"id": "2"},
                {"id": "3"},
            ]
        },
        {
            "results": [
                {"id": "4"},
                {"id": "5"},
            ]
        },
    ]

    crawler.client.get_page_details.side_effect = lambda page_id: {"id": page_id}
    crawler.client.get_attachments.return_value = []

    result = crawler.run(
        batch_size=3,
        max_pages=5,
    )

    assert result == {
        "processed": 5,
        "saved": 5,
        "failed": 0,
    }

    assert crawler.client.get_pages.call_count == 2

    assert crawler.client.get_pages.call_args_list[0].kwargs == {
        "start": 0,
        "limit": 3,
    }

    assert crawler.client.get_pages.call_args_list[1].kwargs == {
        "start": 3,
        "limit": 2,
    }

    assert crawler.page_processor.process.call_count == 5
    assert crawler.client.get_attachments.call_count == 5

    for call in crawler.page_processor.process.call_args_list:
        assert call.args[1]["_attachments"] == []


def test_run_stops_when_confluence_returns_no_pages():
    crawler = KnowledgeCrawler.__new__(KnowledgeCrawler)

    crawler.client = MagicMock()
    crawler.page_processor = MagicMock()
    crawler.checkpoint_repository = MagicMock()
    crawler.sync_id = "DPCC:confluence_delta"

    crawler.client.get_pages.return_value = {"results": []}

    result = crawler.run(
        batch_size=100,
        max_pages=100,
    )

    assert result == {
        "processed": 0,
        "saved": 0,
        "failed": 0,
    }

    crawler.page_processor.process.assert_not_called()


def test_run_rejects_invalid_batch_size():
    crawler = KnowledgeCrawler.__new__(KnowledgeCrawler)

    with pytest.raises(ValueError):
        crawler.run(batch_size=0)


def test_run_rejects_invalid_max_pages():
    crawler = KnowledgeCrawler.__new__(KnowledgeCrawler)

    with pytest.raises(ValueError):
        crawler.run(max_pages=0)


def test_run_advances_checkpoint_after_complete_inventory():
    crawler = KnowledgeCrawler.__new__(KnowledgeCrawler)
    crawler.client = MagicMock()
    crawler.page_processor = MagicMock()
    crawler.checkpoint_repository = MagicMock()
    crawler.sync_id = "DPCC:confluence_delta"

    crawler.client.get_pages.side_effect = [
        {"results": [{"id": "1"}]},
        {"results": []},
    ]
    crawler.client.get_page_details.side_effect = lambda page_id: {
        "id": page_id,
        "version": {"number": 1, "when": "2026-08-09T00:00:00Z"},
    }
    crawler.client.get_attachments.return_value = []

    result = crawler.run(batch_size=100)

    assert result == {"processed": 1, "saved": 1, "failed": 0}
    crawler.checkpoint_repository.save_success.assert_called_once()
    call = crawler.checkpoint_repository.save_success.call_args.kwargs
    assert call["sync_id"] == "DPCC:confluence_delta"
    assert call["processed_pages"] == 1


def test_run_does_not_advance_checkpoint_when_page_fails():
    crawler = KnowledgeCrawler.__new__(KnowledgeCrawler)
    crawler.client = MagicMock()
    crawler.page_processor = MagicMock()
    crawler.checkpoint_repository = MagicMock()
    crawler.sync_id = "DPCC:confluence_delta"

    crawler.client.get_pages.side_effect = [
        {"results": [{"id": "1"}]},
        {"results": []},
    ]
    crawler.client.get_page_details.return_value = {"id": "1"}
    crawler.client.get_attachments.return_value = []
    crawler.page_processor.process.side_effect = RuntimeError("failed")

    result = crawler.run(batch_size=100)

    assert result == {"processed": 1, "saved": 0, "failed": 1}
    crawler.checkpoint_repository.save_success.assert_not_called()
