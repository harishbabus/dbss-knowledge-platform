from datetime import datetime, timezone

from app.connectors.confluence_client import ConfluenceClient

from app.repositories.sync_checkpoint_repository import (
    SyncCheckpointRepository
)

from app.models.sync_checkpoint import (
    SyncCheckpoint
)

from app.utils.logger import logger



class DeltaSyncCrawler:


    def __init__(self):

        self.client = ConfluenceClient()

        self.checkpoint_repo = (
            SyncCheckpointRepository()
        )



    def run(self):


        checkpoint = (
            self.checkpoint_repo
            .get(
                "DPCC"
            )
        )


        if checkpoint:

            last_sync_time = (
                checkpoint["last_sync_time"]
            )

        else:

            logger.info(
                "No checkpoint found. Running from beginning."
            )

            last_sync_time = (
                datetime(
                    2000,
                    1,
                    1,
                    tzinfo=timezone.utc
                )
            )



        logger.info(
            f"Delta sync starting from {last_sync_time}"
        )



        pages = (
            self.client
            .get_pages_modified_after(
                last_sync_time
            )
        )



        results = pages.get(
            "results",
            []
        )



        logger.info(
            f"Pages changed: {len(results)}"
        )



        processed = 0


        for page in results:

            page_id = page["id"]

            logger.info(
                f"Processing changed page {page_id}"
            )


            #
            # Here we will call the existing
            # page + attachment processing logic
            #
            # (next step)
            #


            processed += 1



        #
        # Update checkpoint only after success
        #
        self.checkpoint_repo.save(

            SyncCheckpoint(

                id="DPCC",

                last_sync_time=datetime.now(
                    timezone.utc
                ),

                status="SUCCESS",

                processed_pages=processed,

                last_processed_page=(
                    results[-1]["id"]
                    if results
                    else None
                )

            )
        )


        return {

            "processed": processed

        }