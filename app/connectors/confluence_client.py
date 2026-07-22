import httpx

from app.config.settings import settings


class ConfluenceClient:

    def __init__(self):
        self.base_url = settings.CONFLUENCE_URL
        self.auth = (
            settings.USERNAME,
            settings.PASSWORD
        )

        self.client = httpx.Client(
            auth=self.auth,
            timeout=30
        )


    def get_space(self, space_key=None):

        if space_key is None:
            space_key = settings.SPACE_KEY

        url = (
            f"{self.base_url}"
            f"/rest/api/space/{space_key}"
        )

        response = self.client.get(url)

        response.raise_for_status()

        return response.json()