from datetime import datetime, timezone

from app.config.settings import settings

from app.connectors.confluence_client import ConfluenceClient


from app.models.sync_checkpoint import SyncCheckpoint

from app.services.page_processor import PageProcessor

from app.utils.logger import logger

from app.repositories.sync_checkpoint_repository import (
    SyncCheckpointRepository,
)


class DeltaSyncCrawler:
    def __init__(
        self,
        page_processor: PageProcessor,
    ):
        self.client = ConfluenceClient()

        self.page_processor = page_processor
        self.checkpoint_repo = SyncCheckpointRepository()

    def run(self):
        checkpoint = self.checkpoint_repo.get(settings.SPACE_KEY)

        if checkpoint:
            last_sync_time = checkpoint["last_sync_time"]

        else:
            logger.info("No checkpoint found. Running from beginning.")

            last_sync_time = datetime(2000, 1, 1, tzinfo=timezone.utc)

        logger.info(f"Delta sync starting from {last_sync_time}")

        pages = self.client.get_pages_modified_after(last_sync_time)

        results = pages.get("results", [])

        logger.info(f"Pages changed: {len(results)}")

        processed = 0

        failed = 0

        latest_processed_time = last_sync_time

        for page in results:
            page_id = page["id"]

            logger.info(f"Processing changed page {page_id}")

            try:
                #
                # Reuse the same logic as full inventory
                #
                self.page_processor.process_page(page_id)

                processed += 1

                page_modified = datetime.fromisoformat(
                    page["version"]["when"].replace("Z", "+00:00")
                )

                if page_modified > latest_processed_time:
                    latest_processed_time = page_modified

            except Exception:
                failed += 1

                logger.exception(f"Failed processing page {page_id}")

        #
        # Update checkpoint
        #
        self.checkpoint_repo.save(
            SyncCheckpoint(
                id=settings.SPACE_KEY,
                last_sync_time=latest_processed_time,
                status=("SUCCESS" if failed == 0 else "PARTIAL"),
                processed_pages=processed,
                last_processed_page=(results[-1]["id"] if results else None),
            )
        )

        logger.info(f"""
Delta Sync Complete

Processed : {processed}
Failed    : {failed}
Last Sync : {latest_processed_time}
""")

        return {
            "processed": processed,
            "failed": failed,
            "last_sync_time": latest_processed_time,
        }
