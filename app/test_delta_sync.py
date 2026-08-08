from app.bootstrap.container import Container

container = Container()

crawler = container.delta_sync_crawler

result = crawler.run()


print(result)
