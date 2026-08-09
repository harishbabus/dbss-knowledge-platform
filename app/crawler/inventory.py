from __future__ import annotations

from app.connectors.confluence_client import ConfluenceClient
from app.repositories.sync_checkpoint_repository import SyncCheckpointRepository
from app.services.page_processor import PageProcessor
from app.storage.page_sync_state_repository import PageSyncStateRepository
from app.utils.logger import logger
from datetime import datetime, timezone


class KnowledgeCrawler:
    def __init__(
        self,
        page_processor: PageProcessor,
        sync_state_repository: PageSyncStateRepository | None = None,
        checkpoint_repository: SyncCheckpointRepository | None = None,
        sync_id: str = "DPCC:confluence_delta",
    ) -> None:
        self.client = ConfluenceClient()
        self.page_processor = page_processor
        self.sync_state_repository = sync_state_repository or PageSyncStateRepository()
        self.checkpoint_repository = checkpoint_repository or SyncCheckpointRepository()
        self.sync_id = sync_id

    def run(
        self,
        batch_size: int = 100,
        max_pages: int | None = None,
    ) -> dict[str, int]:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")

        if max_pages is not None and max_pages <= 0:
            raise ValueError("max_pages must be greater than 0")

        if not hasattr(self, "sync_state_repository"):
            self.sync_state_repository = PageSyncStateRepository()
        if not hasattr(self, "checkpoint_repository"):
            self.checkpoint_repository = SyncCheckpointRepository()
        if not hasattr(self, "sync_id"):
            self.sync_id = "DPCC:confluence_delta"

        run_started_at = datetime.now(timezone.utc)
        completed = False
        start = 0
        processed = 0
        saved = 0
        failed = 0

        while True:
            if max_pages is not None:
                remaining = max_pages - processed
                if remaining <= 0:
                    break
                current_batch_size = min(batch_size, remaining)
                progress_total = max_pages
            else:
                current_batch_size = batch_size
                progress_total = None

            logger.info(f"Fetching pages start={start} limit={current_batch_size}")

            response = self.client.get_pages(
                start=start,
                limit=current_batch_size,
            )

            pages = response.get("results", [])
            if not pages:
                completed = True
                break

            for item in pages:
                page_id = str(item["id"])
                page_number = processed + 1

                if progress_total is not None:
                    logger.info(
                        f"Processing page {page_number}/{progress_total} "
                        f"(ID: {page_id})"
                    )
                else:
                    logger.info(f"Processing page {page_number} (ID: {page_id})")

                try:
                    page_data = self.client.get_page_details(page_id)

                    self.page_processor.process(
                        page_id,
                        page_data,
                    )

                    self._save_sync_state(
                        page_id,
                        page_data,
                    )

                    saved += 1

                except Exception as exc:
                    failed += 1
                    logger.error(f"Failed page {page_id}\n\n{exc}")

                processed += 1

            start += len(pages)

            logger.info(
                f"""
Progress:

Processed : {processed}
Saved     : {saved}
Failed    : {failed}
"""
            )

            if len(pages) < current_batch_size:
                # A short final batch proves the complete inventory was reached.
                if max_pages is None:
                    completed = True
                break

        if completed and failed == 0:
            self.checkpoint_repository.save_success(
                sync_id=self.sync_id,
                last_sync_time=run_started_at,
                processed_pages=processed,
            )
            logger.info(
                "Initial inventory completed successfully; "
                f"sync checkpoint advanced to {run_started_at.isoformat()}"
            )
        elif failed > 0:
            logger.warning("Inventory had failures; sync checkpoint was NOT advanced.")

        return {
            "processed": processed,
            "saved": saved,
            "failed": failed,
        }

    def _save_sync_state(
        self,
        page_id: str,
        page_data: dict,
    ) -> None:
        version = page_data.get("version", {}).get("number")
        modified_at = page_data.get("version", {}).get("when")

        self.sync_state_repository.save(
            page_id=page_id,
            version=version,
            modified_at=modified_at,
        )
