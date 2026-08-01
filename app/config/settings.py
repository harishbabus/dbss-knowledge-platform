import os
from dotenv import load_dotenv

load_dotenv()


def required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None:
        raise RuntimeError(f"Required environment variable '{name}' is not set.")

    return value


class Settings:
    CONFLUENCE_URL: str = required_env("CONFLUENCE_URL")

    SPACE_KEY: str = required_env("SPACE_KEY")

    USERNAME: str = required_env("USERNAME")

    PASSWORD: str = required_env("PASSWORD")

    PAGE_LIMIT: int = int(required_env("PAGE_LIMIT"))

    MONGODB_URL: str = required_env("MONGODB_URL")

    DATABASE_NAME: str = required_env("DATABASE_NAME")


settings = Settings()
