from app.bootstrap.container import Container

if __name__ == "__main__":
    container = Container()

    crawler = container.crawler
    result = crawler.run(batch_size=10)

    print("\n====================")
    print("Crawler Result")
    print("====================")

    print(result)
