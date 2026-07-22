import time

from app.connectors.confluence_client import ConfluenceClient
from app.models.page import Page
from app.storage.page_repository import PageRepository
from app.utils.logger import logger


class InventoryCrawler:

    def __init__(self):
        self.client = ConfluenceClient()
        self.repository = PageRepository()

    def crawl_pages(
        self,
        start_page=0,
        max_pages=None,
        page_limit=100,
        sleep_seconds=1,
    ):

        start = start_page
        batch_number = 1

        total_processed = 0
        inserted = 0
        updated = 0
        unchanged = 0
        duplicate_count = 0

        seen_ids = set()

        logger.info("=" * 80)
        logger.info("Starting Confluence Inventory Crawl")
        logger.info("=" * 80)

        while True:

            logger.info(
                f"Fetching Batch {batch_number} | "
                f"Start={start} | Limit={page_limit}"
            )

            response = self.client.get_pages(
                start=start,
                limit=page_limit,
            )

            results = response.get("results", [])

            batch_count = len(results)

            logger.info(f"Received {batch_count} pages")

            if batch_count == 0:
                logger.info("No more pages available.")
                break

            for item in results:

                page_id = str(item["id"])

                if page_id in seen_ids:
                    duplicate_count += 1
                    logger.warning(
                        f"Duplicate page encountered " f"within current run: {page_id}"
                    )
                else:
                    seen_ids.add(page_id)

                page = Page(
                    id=page_id,
                    title=item.get("title"),
                    space=item.get("space", {}).get("key", ""),
                    url=item.get("_links", {}).get("webui"),
                    version=None,
                    created_date=None,
                    updated_date=None,
                )

                result = self.repository.save_page(page)

                if result == "INSERT":
                    inserted += 1

                elif result == "UPDATE":
                    updated += 1

                else:
                    unchanged += 1

                total_processed += 1

                if max_pages is not None and total_processed >= max_pages:
                    logger.info("Maximum page limit reached.")

                    logger.info(f"""
================ SUMMARY ================

Processed : {total_processed}
Inserted : {inserted}
Updated : {updated}
Unchanged : {unchanged}
Duplicates : {duplicate_count}

=========================================
""")

                    return {
                        "processed": total_processed,
                        "inserted": inserted,
                        "updated": updated,
                        "unchanged": unchanged,
                        "duplicates": duplicate_count,
                    }

            logger.info(
                f"Running Total -> "
                f"Processed={total_processed} | "
                f"Inserted={inserted} | "
                f"Updated={updated} | "
                f"Unchanged={unchanged}"
            )

            if batch_count < page_limit:
                logger.info("Last batch reached.")
                break

            start += page_limit
            batch_number += 1

            time.sleep(sleep_seconds)

        logger.info("=" * 80)
        logger.info("Confluence Crawl Completed")
        logger.info("=" * 80)

        logger.info(f"""
================ FINAL SUMMARY ================

Total Processed : {total_processed}

Inserted        : {inserted}

Updated         : {updated}

Unchanged       : {unchanged}

Duplicates      : {duplicate_count}

===============================================
""")

        return {
            "processed": total_processed,
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "duplicates": duplicate_count,
        }
