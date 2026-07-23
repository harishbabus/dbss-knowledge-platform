from app.crawler.delta_sync import DeltaSyncCrawler


crawler = DeltaSyncCrawler()


result = crawler.run()


print(result)