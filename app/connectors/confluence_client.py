import time
import httpx

from app.config.settings import settings
from app.utils.logger import logger


class ConfluenceClient:

    def __init__(self):

        self.base_url = settings.CONFLUENCE_URL

        self.client = httpx.Client(
            auth=(settings.USERNAME, settings.PASSWORD), timeout=60
        )

    def get_pages(self, start=0, limit=100):

        url = (
            f"{self.base_url}"
            f"/rest/api/space/"
            f"{settings.SPACE_KEY}"
            f"/content/page"
        )

        params = {"start": start, "limit": limit}

        retries = 3

        for attempt in range(1, retries + 1):

            try:

                logger.info(f"API request attempt {attempt}")

                response = self.client.get(url, params=params)

                response.raise_for_status()

                return response.json()

            except httpx.RequestError as e:

                logger.warning(f"Request failed: {e}")

                if attempt < retries:

                    wait_time = attempt * 5

                    logger.info(f"Retrying after {wait_time}s")

                    time.sleep(wait_time)

                else:
                    raise
