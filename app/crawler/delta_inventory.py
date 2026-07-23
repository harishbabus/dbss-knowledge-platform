from datetime import datetime, timezone

from app.connectors.confluence_client import ConfluenceClient

from app.repositories.sync_checkpoint_repository import (
    SyncCheckpointRepository
)

from app.models.sync_checkpoint import (
    SyncCheckpoint
)

from app.utils.logger import logger



class DeltaCrawler:


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

            last_sync = (
                checkpoint["last_sync_time"]
            )

        else:

            last_sync = (
                "2000-01-01 00:00"
            )


        logger.info(
            f"Delta sync from {last_sync}"
        )


        pages = (
            self.client
            .get_pages_modified_after(
                last_sync
            )
        )


        results = pages.get(
            "results",
            []
        )


        logger.info(
            f"Changed pages: {len(results)}"
        )


        #
        # Next step:
        # call existing inventory processing
        #
        

        self.checkpoint_repo.save(

            SyncCheckpoint(

                id="DPCC",

                last_sync_time=datetime.now(
                    timezone.utc
                ),

                status="SUCCESS",

                processed_pages=len(results)

            )
        )