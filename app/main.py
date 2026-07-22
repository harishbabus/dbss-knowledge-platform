from app.crawler.inventory import KnowledgeCrawler

from app.utils.logger import logger



def main():


    crawler = KnowledgeCrawler()


    result = crawler.run(
        batch_size=100
    )


    logger.info(
        result
    )



if __name__ == "__main__":

    main()