from app.bootstrap.container import Container
from app.utils.logger import logger


def main():
    container = Container()

    result = container.crawler.run(batch_size=100)

    logger.info(result)


if __name__ == "__main__":
    main()
