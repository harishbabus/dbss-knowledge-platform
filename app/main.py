from app.crawler.inventory import InventoryCrawler
from app.storage.csv_writer import save_pages


def main():

    print("Starting Confluence crawl...")

    crawler = InventoryCrawler()

    count = crawler.crawl_pages()

    print(
        f"Pages processed: {count}"
    )

    save_pages(pages, "data/inventory/confluence_inventory.csv")

    print("Inventory completed")


if __name__ == "__main__":
    main()
