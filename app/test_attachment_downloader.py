from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.connectors.attachment_downloader import (
    AttachmentDownloader,
    DownloadResult,
)
from app.models.attachment import Attachment


def _attachment(
    *,
    attachment_id="att-1",
    page_id="page-1",
    filename="test.pdf",
    download_url="/download/test.pdf",
):
    return Attachment(
        id=attachment_id,
        page_id=page_id,
        filename=filename,
        media_type="application/pdf",
        size=4,
        download_url=download_url,
        version=1,
    )


def _response(data):
    response = MagicMock()
    response.status_code = 200
    response.iter_bytes.return_value = data
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_download_success_writes_binary_and_returns_path(tmp_path):
    attachment = _attachment()
    response = _response([b"PDF", b"1"])

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=1, retry_delays=(0,)
    )

    with patch(
        "app.connectors.attachment_downloader.httpx.stream",
        return_value=response,
    ):
        path = downloader.download(attachment)

    assert path == tmp_path / "page-1" / "att-1_test.pdf"
    assert path.read_bytes() == b"PDF1"


def test_download_with_metadata_calculates_hash_and_size(tmp_path):
    attachment = _attachment()
    response = _response([b"hello", b" world"])

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=1, retry_delays=(0,)
    )

    with patch(
        "app.connectors.attachment_downloader.httpx.stream",
        return_value=response,
    ):
        result = downloader.download_with_metadata(attachment)

    assert isinstance(result, DownloadResult)
    assert result is not None
    assert result.file_path.read_bytes() == b"hello world"
    assert result.size == 11
    assert result.content_hash == (
        "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    )


def test_download_returns_none_without_download_url(tmp_path):
    attachment = _attachment(download_url=None)

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=1, retry_delays=(0,)
    )

    assert downloader.download(attachment) is None


def test_download_rejects_non_retryable_http_error(tmp_path):
    attachment = _attachment()
    response = MagicMock()
    response.status_code = 404
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=response
    )

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=3, retry_delays=(0,)
    )

    with patch(
        "app.connectors.attachment_downloader.httpx.stream",
        return_value=response,
    ):
        with pytest.raises(httpx.HTTPStatusError):
            downloader.download(attachment)

    assert list(tmp_path.rglob("*.part")) == []


def test_download_retries_transient_http_error(tmp_path):
    attachment = _attachment()

    failing = MagicMock()
    failing.status_code = 503
    failing.__enter__.return_value = failing
    failing.__exit__.return_value = False
    failing.raise_for_status.side_effect = httpx.HTTPStatusError(
        "503", request=MagicMock(), response=failing
    )

    success = _response([b"data"])

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=2, retry_delays=(0,)
    )

    with patch(
        "app.connectors.attachment_downloader.httpx.stream",
        side_effect=[failing, success],
    ) as stream:
        with patch("app.connectors.attachment_downloader.time.sleep"):
            path = downloader.download(attachment)

    assert path is not None
    assert path.read_bytes() == b"data"
    assert stream.call_count == 2


def test_download_retries_timeout(tmp_path):
    attachment = _attachment()
    success = _response([b"ok"])

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=2, retry_delays=(0,)
    )

    with patch(
        "app.connectors.attachment_downloader.httpx.stream",
        side_effect=[httpx.ReadTimeout("timed out"), success],
    ):
        with patch("app.connectors.attachment_downloader.time.sleep"):
            path = downloader.download(attachment)

    assert path is not None
    assert path.read_bytes() == b"ok"


def test_failed_download_does_not_leave_partial_file(tmp_path):
    attachment = _attachment()
    response = MagicMock()
    response.status_code = 200
    response.__enter__.return_value = response
    response.__exit__.return_value = False

    def broken_chunks():
        yield b"partial"
        raise httpx.ReadError("connection lost")

    response.iter_bytes.return_value = broken_chunks()

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=1, retry_delays=(0,)
    )

    with patch(
        "app.connectors.attachment_downloader.httpx.stream",
        return_value=response,
    ):
        with pytest.raises(httpx.ReadError):
            downloader.download(attachment)

    assert list(tmp_path.rglob("*.part")) == []
    assert not (tmp_path / "page-1" / "att-1_test.pdf").exists()


def test_download_sanitizes_filename(tmp_path):
    attachment = _attachment(filename="../../unsafe folder/report.pdf")
    response = _response([b"x"])

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=1, retry_delays=(0,)
    )

    with patch(
        "app.connectors.attachment_downloader.httpx.stream",
        return_value=response,
    ):
        path = downloader.download(attachment)

    assert path is not None
    assert path.parent == tmp_path / "page-1"
    assert path.name == "att-1_report.pdf"


def test_download_accepts_absolute_download_url(tmp_path):
    attachment = _attachment(download_url="https://wiki.example.com/download/test.pdf")
    response = _response([b"x"])

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=1, retry_delays=(0,)
    )

    with patch(
        "app.connectors.attachment_downloader.httpx.stream",
        return_value=response,
    ) as stream:
        path = downloader.download(attachment)

    assert path is not None
    assert stream.call_args.args[1] == ("https://wiki.example.com/download/test.pdf")


def test_download_retries_temporary_file_os_error(tmp_path):
    attachment = _attachment()
    first = _response([b"first"])
    second = _response([b"second"])

    downloader = AttachmentDownloader(
        download_dir=tmp_path, retries=2, retry_delays=(0,)
    )

    original_replace = __import__("pathlib").Path.replace
    calls = {"count": 0}

    def flaky_replace(self, target):
        calls["count"] += 1
        if calls["count"] == 1:
            raise FileNotFoundError("temporary file disappeared")
        return original_replace(self, target)

    with (
        patch(
            "app.connectors.attachment_downloader.httpx.stream",
            side_effect=[first, second],
        ),
        patch(
            "app.connectors.attachment_downloader.Path.replace",
            new=flaky_replace,
        ),
        patch("app.connectors.attachment_downloader.time.sleep"),
    ):
        path = downloader.download(attachment)

    assert path is not None
    assert path.read_bytes() == b"second"
    assert calls["count"] == 2
    assert list(tmp_path.rglob("*.part")) == []
