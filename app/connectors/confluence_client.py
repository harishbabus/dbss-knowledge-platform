import httpx

from app.config.settings import settings
from app.utils.logger import logger
from datetime import datetime

class ConfluenceClient:

    def __init__(self):

        self.base_url = settings.CONFLUENCE_URL.rstrip("/")

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

        response = self.client.get(url, params=params)

        response.raise_for_status()

        return response.json()

    def get_pages_modified_after(self, modified_after):

        logger.info(f"Fetching pages modified after {modified_after}")

        if isinstance(modified_after, datetime):
            modified_after = (
                modified_after
                .strftime("%Y-%m-%d %H:%M")
            )

        cql = (
            f"type=page "
            f'AND space="{settings.SPACE_KEY}" '
            f'AND lastModified > "{modified_after}"'
        )

        logger.info(f"CQL Query: {cql}")

        response = self.client.get(
            f"{self.base_url}/rest/api/content/search",
            params={"cql": cql, "limit": 100, "expand": "version"},
        )

        logger.info(f"Confluence response: {response.status_code}")

        if response.status_code != 200:

            logger.error(response.text)

            response.raise_for_status()

        return response.json()

    def get_page_details(self, page_id):

        logger.info(f"Fetching details for page {page_id}")

        url = f"{self.base_url}" f"/rest/api/content/" f"{page_id}"

        params = {
            "expand": ",".join(
                ["body.storage", "version", "history", "ancestors", "metadata.labels"]
            )
        }

        response = self.client.get(url, params=params)

        response.raise_for_status()

        return response.json()

    def get_attachments(self, page_id: str):

        logger.info(f"Fetching attachments for page {page_id}")

        url = f"{self.base_url}/rest/api/content/" f"{page_id}/child/attachment"

        params = {"limit": 100}

        response = self.client.get(url, params=params)

        response.raise_for_status()

        data = response.json()

        attachments = []

        for item in data.get("results", []):

            attachment = {
                "id": item.get("id"),
                "filename": item.get("title"),
                "media_type": item.get("metadata", {}).get("mediaType"),
                "size": item.get("extensions", {}).get("fileSize"),
                "labels": [
                    label.get("name")
                    for label in item.get("metadata", {})
                    .get("labels", {})
                    .get("results", [])
                ],
                "download_url": item.get("_links", {}).get("download"),
                "thumbnail_url": item.get("_links", {}).get("thumbnail"),
                "status": item.get("status"),
            }

            attachments.append(attachment)

        logger.info(f"Found {len(attachments)} attachments")

        return attachments

    def get_labels(self, page_id):

        logger.info(f"Fetching labels " f"for page {page_id}")

        url = f"{self.base_url}" f"/rest/api/content/" f"{page_id}" f"/label"

        response = self.client.get(url)

        response.raise_for_status()

        return response.json()
