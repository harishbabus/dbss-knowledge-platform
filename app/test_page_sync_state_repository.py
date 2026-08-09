from unittest.mock import MagicMock

from app.storage.page_sync_state_repository import PageSyncStateRepository


def test_get_reads_by_page_id():
    repository = PageSyncStateRepository.__new__(PageSyncStateRepository)
    repository.collection = MagicMock()

    repository.get("123")

    repository.collection.find_one.assert_called_once_with({"page_id": "123"})


def test_save_uses_upsert():
    repository = PageSyncStateRepository.__new__(PageSyncStateRepository)
    repository.collection = MagicMock()

    repository.save(
        page_id="123",
        version=7,
        modified_at="2026-08-09T01:00:00Z",
    )

    call = repository.collection.update_one.call_args

    assert call.args[0] == {"page_id": "123"}
    assert call.kwargs["upsert"] is True
    assert call.args[1]["$set"]["version"] == 7
