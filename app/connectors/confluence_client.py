from __future__ import annotations

import time
from typing import Any

import httpx

from app.config.settings import settings
from app.utils.logger import logger


class ConfluenceClient:
    def __init__(
        self,
        timeout: float = 60.0,
        retries: int = 3,
        retry_delays: tuple[float, ...] = (2.0, 5.0, 10.0),
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        if retries <= 0:
            raise ValueError("retries must be greater than 0")
        if not retry_delays:
            raise ValueError("retry_delays cannot be empty")

        self.base_url = settings.CONFLUENCE_URL.rstrip("/")
        self.content_url = f"{self.base_url}/rest/api/content"
        self.space_url = f"{self.base_url}/rest/api/space/{settings.SPACE_KEY}"
        self.retries = retries
        self.retry_delays = retry_delays

        self.client = httpx.Client(
            auth=(settings.USERNAME, settings.PASSWORD),
            timeout=timeout,
            follow_redirects=True,
        )

    def _get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_exception: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                response = self.client.get(url, params=params)

                if 400 <= response.status_code < 500:
                    response.raise_for_status()

                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError as exc:
                    raise ValueError("Confluence returned a non-JSON response") from exc

                if not isinstance(data, dict):
                    raise ValueError("Confluence returned an unexpected JSON payload")

                return data

            except httpx.HTTPStatusError as exc:
                if exc.response is not None and exc.response.status_code < 500:
                    logger.error(
                        f"GET failed with non-retryable HTTP status: "
                        f"{exc.response.status_code} URL={url}"
                    )
                    raise
                last_exception = exc

            except (httpx.TimeoutException, httpx.RequestError, ValueError) as exc:
                last_exception = exc

            logger.warning(
                f"""
GET failed

URL      : {url}
Attempt  : {attempt}/{self.retries}
Reason   : {last_exception}
"""
            )

            if attempt < self.retries:
                delay = self.retry_delays[min(attempt - 1, len(self.retry_delays) - 1)]
                logger.info(f"Retrying GET in {delay:g} seconds")
                time.sleep(delay)

        assert last_exception is not None
        raise last_exception

    def get_pages(self, start: int = 0, limit: int = 100) -> dict[str, Any]:
        return self._get(
            f"{self.space_url}/content/page",
            params={"start": start, "limit": limit},
        )

    def get_pages_modified_after(
        self,
        modified_after: Any,
        *,
        start: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        if hasattr(modified_after, "strftime"):
            modified_after = modified_after.strftime("%Y-%m-%d %H:%M")

        if start < 0:
            raise ValueError("start cannot be negative")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        logger.info(
            f"Fetching pages modified after {modified_after} "
            f"(start={start}, limit={limit})"
        )

        cql = (
            f"type=page "
            f'AND space="{settings.SPACE_KEY}" '
            f'AND lastModified > "{modified_after}"'
        )

        logger.info(f"CQL Query: {cql}")

        return self._get(
            f"{self.content_url}/search",
            params={
                "cql": cql,
                "start": start,
                "limit": limit,
                "expand": "version",
            },
        )

    def get_page_details(self, page_id: str) -> dict[str, Any]:
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

    def get_attachments(self, page_id: str) -> list[dict[str, Any]]:
        logger.info(f"Fetching attachments for page {page_id}")

        attachments: list[dict[str, Any]] = []
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

    def get_labels(self, page_id: str) -> dict[str, Any]:
        logger.info(f"Fetching labels for page {page_id}")
        return self._get(f"{self.content_url}/{page_id}/label")
