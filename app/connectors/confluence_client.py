import time

import httpx

from app.config.settings import settings
from app.utils.logger import logger


class ConfluenceClient:

    def __init__(self):

        self.base_url = settings.CONFLUENCE_URL.rstrip("/")

        self.content_url = f"{self.base_url}/rest/api/content"

        self.space_url = f"{self.base_url}/rest/api/space/{settings.SPACE_KEY}"

        self.client = httpx.Client(
            auth=(settings.USERNAME, settings.PASSWORD),
            timeout=60,
            follow_redirects=True,
        )

    def _get(self, url, params=None, retries=3):

        last_exception = None

        for attempt in range(retries):

            try:

                response = self.client.get(url, params=params)

                response.raise_for_status()

                return response.json()

            except Exception as e:

                last_exception = e

                logger.warning(f"""
GET failed

URL      : {url}
Attempt  : {attempt + 1}/{retries}
Reason   : {e}
""")

                if attempt < retries - 1:

                    time.sleep(2)

        raise last_exception

    def get_pages(self, start=0, limit=100):

        return self._get(
            f"{self.space_url}/content/page", params={"start": start, "limit": limit}
        )

    def get_pages_modified_after(self, modified_after):

        if hasattr(modified_after, "strftime"):

            modified_after = modified_after.strftime("%Y-%m-%d %H:%M")

        logger.info(f"Fetching pages modified after {modified_after}")

        cql = (
            f"type=page "
            f'AND space="{settings.SPACE_KEY}" '
            f'AND lastModified > "{modified_after}"'
        )

        logger.info(f"CQL Query: {cql}")

        return self._get(
            f"{self.content_url}/search",
            params={"cql": cql, "limit": 100, "expand": "version"},
        )

    def get_page_details(self, page_id):

        logger.info(f"Fetching details for page {page_id}")

        return self._get(
            f"{self.content_url}/{page_id}",
            params={
                "expand": ",".join(
                    [
                        "body.storage",
                        "version",
                        "history",
                        "ancestors",
                        "metadata.labels",
                        "space",
                    ]
                )
            },
        )

    def get_attachments(self, page_id):

        logger.info(f"Fetching attachments for page {page_id}")

        attachments = []

        start = 0

        limit = 100

        while True:

            data = self._get(
                f"{self.content_url}/{page_id}/child/attachment",
                params={
                    "start": start,
                    "limit": limit,
                    "expand": "version,metadata.labels",
                },
            )

            results = data.get("results", [])

            if not results:

                break

            for item in results:

                attachments.append(
                    {
                        "id": item.get("id"),
                        "filename": item.get("title"),
                        "media_type": item.get("metadata", {}).get("mediaType"),
                        "size": item.get("extensions", {}).get("fileSize"),
                        "status": item.get("status"),
                        "labels": [
                            label.get("name")
                            for label in item.get("metadata", {})
                            .get("labels", {})
                            .get("results", [])
                        ],
                        "download_url": item.get("_links", {}).get("download"),
                        "thumbnail_url": item.get("_links", {}).get("thumbnail"),
                        "version": item.get("version", {}).get("number"),
                        "version_when": item.get("version", {}).get("when"),
                        "version_by": item.get("version", {})
                        .get("by", {})
                        .get("displayName"),
                    }
                )

            start += limit

        logger.info(f"Found {len(attachments)} attachments")

        return attachments

    def get_labels(self, page_id):

        logger.info(f"Fetching labels for page {page_id}")

        return self._get(f"{self.content_url}/{page_id}/label")
