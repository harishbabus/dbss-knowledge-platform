from __future__ import annotations

from app.connectors.confluence_client import ConfluenceClient
from app.services.page_processor import PageProcessor
from app.utils.logger import logger


class KnowledgeCrawler:
    def __init__(self, page_processor: PageProcessor):
        self.client = ConfluenceClient()
        self.page_processor = page_processor

    def run(
        self,
        batch_size: int = 100,
        max_pages: int | None = None,
    ) -> dict[str, int]:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")

        if max_pages is not None and max_pages <= 0:
            raise ValueError("max_pages must be greater than 0")

        start = 0
        processed = 0
        saved = 0
        failed = 0

        while True:
            if max_pages is not None:
                remaining = max_pages - processed
                if remaining <= 0:
                    break

                current_batch_size = min(
                    batch_size,
                    remaining,
                )
                progress_total = max_pages
            else:
                current_batch_size = batch_size
                progress_total = None

            logger.info(f"Fetching pages start={start} limit={current_batch_size}")

            response = self.client.get_pages(
                start=start,
                limit=current_batch_size,
            )

            pages = response.get(
                "results",
                [],
            )

            if not pages:
                break

            for item in pages:
                page_id = item["id"]
                page_number = processed + 1

                if progress_total is not None:
                    logger.info(
                        f"Processing page "
                        f"{page_number}/{progress_total} "
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

                    saved += 1

                except Exception as exc:
                    failed += 1

                    logger.error(
                        f"""
Failed page {page_id}

{exc}
"""
                    )

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
                break

        return {
            "processed": processed,
            "saved": saved,
            "failed": failed,
        }
