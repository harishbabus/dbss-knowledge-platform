from app.crawler.inventory import KnowledgeCrawler

if __name__ == "__main__":

    crawler = KnowledgeCrawler()

    result = crawler.run(batch_size=10)

    print("\n====================")
    print("Crawler Result")
    print("====================")

    print(result)
