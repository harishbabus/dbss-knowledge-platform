from __future__ import annotations

from datetime import datetime, timezone

from app.config.settings import settings
from app.connectors.confluence_client import ConfluenceClient
from app.repositories.sync_checkpoint_repository import SyncCheckpointRepository
from app.services.page_processor import PageProcessor
from app.storage.page_sync_state_repository import PageSyncStateRepository
from app.utils.logger import logger


class DeltaSyncCrawler:
    """Processes changed Confluence pages and maintains a global watermark."""

    DEFAULT_SYNC_ID = "confluence_delta"

    def __init__(
        self,
        page_processor: PageProcessor,
        sync_state_repository: PageSyncStateRepository | None = None,
        checkpoint_repository: SyncCheckpointRepository | None = None,
        sync_id: str | None = None,
    ) -> None:
        self.client = ConfluenceClient()
        self.page_processor = page_processor
        self.sync_state_repository = sync_state_repository or PageSyncStateRepository()
        self.checkpoint_repository = checkpoint_repository or SyncCheckpointRepository()
        self.sync_id = sync_id or f"{settings.SPACE_KEY}:{self.DEFAULT_SYNC_ID}"

    @staticmethod
    def _format_modified_after(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")

    def _resolve_modified_after(
        self,
        modified_after: str | datetime | None,
    ) -> str:
        if modified_after is not None:
            if isinstance(modified_after, datetime):
                return self._format_modified_after(modified_after)

            if not isinstance(modified_after, str):
                raise TypeError("modified_after must be a string or datetime")

            if not modified_after.strip():
                raise ValueError("modified_after cannot be empty")

            return modified_after.strip()

        checkpoint = self.checkpoint_repository.get_last_successful(self.sync_id)

        if checkpoint is None:
            raise ValueError(
                "No successful sync checkpoint exists. "
                "Run an initial inventory crawl first or provide modified_after."
            )

        resolved = self._format_modified_after(checkpoint)

        logger.info(
            f"Using last successful sync checkpoint: {resolved} "
            f"(sync_id={self.sync_id})"
        )

        return resolved

    def run(
        self,
        modified_after: str | datetime | None = None,
        *,
        batch_size: int = 100,
    ) -> dict[str, int | bool | str]:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        resolved_modified_after = self._resolve_modified_after(modified_after)

        # Capture the watermark before querying Confluence. Changes made
        # during this run are intentionally left for the next run.
        run_started_at = datetime.now(timezone.utc)

        processed = 0
        skipped = 0
        saved = 0
        failed = 0
        candidates = 0
        start = 0
        last_processed_page: str | None = None

        while True:
            response = self.client.get_pages_modified_after(
                resolved_modified_after,
                start=start,
                limit=batch_size,
            )

            pages = response.get("results", [])

            if not pages:
                break

            batch_count = len(pages)
            candidates += batch_count

            logger.info(f"Delta batch: start={start}, count={batch_count}")

            for index, item in enumerate(pages, start=start + 1):
                page_id = str(item["id"])

                logger.info(f"Delta page {index}/{start + batch_count} (ID: {page_id})")

                try:
                    page_data = self.client.get_page_details(page_id)

                    version = page_data.get("version", {}).get("number")
                    previous = self.sync_state_repository.get(page_id)

                    same_version = (
                        previous is not None and previous.get("version") == version
                    )

                    retryable_attachments = False
                    if same_version:
                        retryable_attachments = (
                            self.page_processor.attachment_repo.has_retryable_by_page(
                                page_id
                            )
                        )

                    if same_version and not retryable_attachments:
                        skipped += 1
                        logger.info(
                            f"Skipping unchanged page {page_id} (version {version})"
                        )
                        continue

                    if same_version and retryable_attachments:
                        logger.info(
                            f"Retrying attachment failures for unchanged page "
                            f"{page_id} (version {version})"
                        )

                    # Changed/new pages and pages with retryable attachment
                    # failures need current attachment discovery.
                    page_data["_attachments"] = self.client.get_attachments(page_id)

                    self.page_processor.process(page_id, page_data)

                    self.sync_state_repository.save(
                        page_id=page_id,
                        version=version,
                        modified_at=page_data.get("version", {}).get("when"),
                    )

                    processed += 1
                    saved += 1
                    last_processed_page = page_id

                except Exception as exc:
                    failed += 1
                    logger.error(f"Failed delta page {page_id}\n\n{exc}")

            if batch_count < batch_size:
                break

            start += batch_count

        checkpoint_updated = False

        if failed == 0:
            self.checkpoint_repository.save_success(
                sync_id=self.sync_id,
                last_sync_time=run_started_at,
                processed_pages=processed,
                last_processed_page=last_processed_page,
            )
            checkpoint_updated = True
            logger.info(
                f"Advanced sync checkpoint to "
                f"{self._format_modified_after(run_started_at)}"
            )
        else:
            logger.warning("Delta sync had failures; sync checkpoint was NOT advanced.")

        logger.info(
            f"""
Delta sync complete:

Candidates          : {candidates}
Processed           : {processed}
Skipped             : {skipped}
Saved               : {saved}
Failed              : {failed}
Checkpoint updated : {checkpoint_updated}
"""
        )

        return {
            "candidates": candidates,
            "processed": processed,
            "skipped": skipped,
            "saved": saved,
            "failed": failed,
        }
