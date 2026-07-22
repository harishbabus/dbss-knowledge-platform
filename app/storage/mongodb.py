from pymongo import MongoClient

from app.config.settings import settings
from app.utils.logger import logger


class MongoDB:

    def __init__(self):

        logger.info(
            "Connecting to MongoDB..."
        )

        self.client = MongoClient(
            settings.MONGODB_URL
        )

        self.db = self.client[
            settings.DATABASE_NAME
        ]

        logger.info(
            f"Connected to database: "
            f"{settings.DATABASE_NAME}"
        )


    def collection(self, name):

        return self.db[name]


mongodb = MongoDB()