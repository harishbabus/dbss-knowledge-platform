import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")

    SPACE_KEY = os.getenv("SPACE_KEY")

    USERNAME = os.getenv("USERNAME")

    PASSWORD = os.getenv("PASSWORD")

    PAGE_LIMIT = int(
        os.getenv("PAGE_LIMIT", 100)
    )

    MONGODB_URL = os.getenv(
        "MONGODB_URL"
    )

    DATABASE_NAME = os.getenv(
        "DATABASE_NAME"
    )


settings = Settings()