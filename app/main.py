from app.crawler.inventory import InventoryCrawler
from app.utils.logger import logger


def main():

    logger.info("Starting DBSS Knowledge Platform ingestion")

    crawler = InventoryCrawler()

    result = crawler.crawl_pages(start_page=0, max_pages=None, page_limit=100)

    logger.info("Inventory completed")

    logger.info(f"""
==============================
SYNC SUMMARY

Processed : {result["processed"]}
Inserted  : {result["inserted"]}
Updated   : {result["updated"]}
Unchanged : {result["unchanged"]}
Duplicates: {result["duplicates"]}

==============================
""")


if __name__ == "__main__":
    main()
