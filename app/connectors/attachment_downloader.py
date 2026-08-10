from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.config.settings import settings
from app.utils.logger import logger


@dataclass(frozen=True)
class DownloadResult:
    """Result of a successful attachment download."""

    file_path: Path
    content_hash: str
    size: int


class AttachmentDownloader:
    """
    Safely downloads Confluence attachments.

    The existing download() contract is preserved: it returns Path | None.
    download_with_metadata() additionally returns SHA-256 and byte size.
    """

    def __init__(
        self,
        *,
        download_dir: str | Path = "downloads",
        timeout: float = 120.0,
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
        self.auth = (settings.USERNAME, settings.PASSWORD)
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retries = retries
        self.retry_delays = retry_delays

    def download(self, attachment: Any) -> Path | None:
        result = self.download_with_metadata(attachment)
        return result.file_path if result is not None else None

    def download_with_metadata(
        self,
        attachment: Any,
    ) -> DownloadResult | None:
        download_url = getattr(attachment, "download_url", None)

        if not download_url:
            filename = getattr(attachment, "filename", "<unknown>")
            logger.warning(f"No download URL for {filename}")
            return None

        filename = self._safe_filename(getattr(attachment, "filename", "attachment"))
        page_id = self._safe_component(getattr(attachment, "page_id", "unknown-page"))
        attachment_id = self._safe_component(
            getattr(attachment, "id", "unknown-attachment")
        )

        target_dir = self.download_dir / page_id
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / f"{attachment_id}_{filename}"
        url = self._build_url(str(download_url))

        logger.info(f"Downloading attachment {filename} (ID: {attachment_id})")

        last_exception: Exception | None = None

        for attempt in range(1, self.retries + 1):
            # A fresh temporary path per attempt prevents a failed/aborted
            # attempt from interfering with a later retry. This is especially
            # important on Windows where another handle may briefly retain a
            # previous .part file.
            temp_path = file_path.with_name(f".{file_path.name}.{time.time_ns()}.part")

            try:
                content_hash = hashlib.sha256()
                total_size = 0

                with httpx.stream(
                    "GET",
                    url,
                    auth=self.auth,
                    timeout=self.timeout,
                    follow_redirects=True,
                ) as response:
                    if 400 <= response.status_code < 500:
                        response.raise_for_status()

                    response.raise_for_status()

                    with temp_path.open("wb") as output:
                        for chunk in response.iter_bytes():
                            if not chunk:
                                continue
                            output.write(chunk)
                            content_hash.update(chunk)
                            total_size += len(chunk)

                # Atomic finalization: the completed file becomes visible only
                # after the entire response has been written successfully.
                temp_path.replace(file_path)

                digest = content_hash.hexdigest()

                logger.info(
                    f"Saved attachment to {file_path} "
                    f"(size={total_size}, sha256={digest})"
                )

                return DownloadResult(
                    file_path=file_path,
                    content_hash=digest,
                    size=total_size,
                )

            except httpx.HTTPStatusError as exc:
                last_exception = exc
                if exc.response is not None and exc.response.status_code < 500:
                    logger.error(
                        "Attachment download failed with "
                        f"non-retryable HTTP status: "
                        f"{exc.response.status_code} URL={url}"
                    )
                    raise

            except (httpx.TimeoutException, httpx.RequestError, OSError) as exc:
                # OSError covers local filesystem failures involving the
                # temporary file. Those are retryable because a subsequent
                # attempt receives a fresh .part path.
                last_exception = exc

            finally:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        logger.warning(f"Could not remove temporary file: {temp_path}")

            logger.warning(
                f"Attachment download failed "
                f"(attempt {attempt}/{self.retries}): {last_exception}"
            )

            if attempt < self.retries:
                delay = self.retry_delays[min(attempt - 1, len(self.retry_delays) - 1)]
                logger.info(f"Retrying attachment download in {delay:g} seconds")
                time.sleep(delay)

        assert last_exception is not None
        raise last_exception

    def _build_url(self, download_url: str) -> str:
        if download_url.startswith(("http://", "https://")):
            return download_url
        return f"{self.base_url}/{download_url.lstrip('/')}"

    @staticmethod
    def _safe_component(value: str) -> str:
        value = str(value).strip()
        if not value:
            return "unknown"
        return re.sub(r"[^A-Za-z0-9._-]+", "_", value)

    @classmethod
    def _safe_filename(cls, filename: str) -> str:
        return cls._safe_component(Path(str(filename)).name)
