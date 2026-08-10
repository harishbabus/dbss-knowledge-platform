import zipfile

from app.extractors.attachment_content_extractor import AttachmentContentExtractor
from app.models.attachment import Attachment
from app.models.attachment_processing_result import AttachmentProcessingStatus
from app.models.content_type import ContentType


def attachment(filename):
    return Attachment(id="1", page_id="p", filename=filename)


def test_ldif_is_supported(tmp_path):
    path = tmp_path / "permission.ldif"
    path.write_text("dn: uid=test,dc=example\nuid: test\n", encoding="utf-8")
    status, content, error = AttachmentContentExtractor().extract_with_status(
        attachment(path.name), path
    )
    assert status == AttachmentProcessingStatus.SUCCESS
    assert content.content_type == ContentType.LDIF
    assert "uid: test" in content.text
    assert error is None


def test_invalid_json_falls_back_to_raw_text(tmp_path):
    path = tmp_path / "notification.json"
    path.write_text('{\n  "name": value\n}\n', encoding="utf-8")
    status, content, _ = AttachmentContentExtractor().extract_with_status(
        attachment(path.name), path
    )
    assert status == AttachmentProcessingStatus.SUCCESS
    assert content.content_type == ContentType.JSON
    assert content.metadata["json_parsed"] is False
    assert "name" in content.text


def test_unknown_extension_text_fallback(tmp_path):
    path = tmp_path / "Master_data"
    path.write_text("customer_id | 1001\nstatus | ACTIVE\n", encoding="utf-8")
    status, content, _ = AttachmentContentExtractor().extract_with_status(
        attachment(path.name), path
    )
    assert status == AttachmentProcessingStatus.SUCCESS
    assert content.content_type == ContentType.TEXT


def test_zip_limits_are_enforced(tmp_path):
    path = tmp_path / "large.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for i in range(3):
            zf.writestr(f"{i}.txt", "x")
    extractor = AttachmentContentExtractor()
    extractor.MAX_ARCHIVE_FILES = 2
    status, content, error = extractor.extract_with_status(attachment(path.name), path)
    assert status == AttachmentProcessingStatus.EXTRACTION_FAILED
    assert content is None
    assert "limit" in error


def test_zip_expanded_limit_can_handle_large_internal_content(tmp_path):
    path = tmp_path / "large-expanded.zip"
    payload = "x" * (51 * 1024 * 1024)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("large.txt", payload)

    extractor = AttachmentContentExtractor()
    status, content, error = extractor.extract_with_status(attachment(path.name), path)

    assert status == AttachmentProcessingStatus.SUCCESS
    assert content is not None
    assert len(content.text) == len(payload) + len("FILE: large.txt")
    assert error is None


def test_svg_payload_with_png_extension_uses_text_fallback(tmp_path):
    path = tmp_path / "image.png"
    path.write_text(
        '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">'
        "<text>hello knowledge platform</text></svg>",
        encoding="utf-8",
    )

    status, content, error = AttachmentContentExtractor().extract_with_status(
        attachment(path.name), path
    )

    assert status == AttachmentProcessingStatus.SUCCESS
    assert content is not None
    assert content.metadata["format"] == "svg"
    assert "hello knowledge platform" in content.text
    assert error is None
