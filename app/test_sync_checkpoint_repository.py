from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.repositories.sync_checkpoint_repository import SyncCheckpointRepository


def _repo():
    repo = SyncCheckpointRepository.__new__(SyncCheckpointRepository)
    repo.collection = MagicMock()
    return repo


def test_get_last_successful_returns_datetime():
    repo = _repo()
    value = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
    repo.collection.find_one.return_value = {
        "_id": "DPCC:confluence_delta",
        "status": "SUCCESS",
        "last_sync_time": value,
    }

    assert repo.get_last_successful("DPCC:confluence_delta") == value


def test_get_last_successful_returns_none_for_missing_checkpoint():
    repo = _repo()
    repo.collection.find_one.return_value = None

    assert repo.get_last_successful("DPCC:confluence_delta") is None


def test_get_last_successful_returns_none_for_failed_checkpoint():
    repo = _repo()
    repo.collection.find_one.return_value = {
        "_id": "DPCC:confluence_delta",
        "status": "FAILED",
        "last_sync_time": datetime.now(timezone.utc),
    }

    assert repo.get_last_successful("DPCC:confluence_delta") is None


def test_save_success_uses_upsert():
    repo = _repo()
    value = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)

    repo.save_success(
        "DPCC:confluence_delta",
        value,
        processed_pages=10,
        last_processed_page="123",
    )

    repo.collection.update_one.assert_called_once()
    args = repo.collection.update_one.call_args

    assert args.args[0] == {"_id": "DPCC:confluence_delta"}
    assert args.kwargs["upsert"] is True
    assert args.args[1]["$set"]["last_sync_time"] == value
    assert args.args[1]["$set"]["status"] == "SUCCESS"
    assert args.args[1]["$set"]["processed_pages"] == 10
    assert args.args[1]["$set"]["last_processed_page"] == "123"
