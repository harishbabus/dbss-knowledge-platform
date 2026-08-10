from app.extractors.attachment_content_extractor import AttachmentContentExtractor
from app.models.attachment import Attachment


def test_text_attachment_extracts_from_explicit_path(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("hello knowledge platform", encoding="utf-8")

    attachment = Attachment(
        id="att-1",
        page_id="page-1",
        filename="sample.txt",
    )

    content = AttachmentContentExtractor().extract(attachment, file_path=path)

    assert content is not None
    assert content.text == "hello knowledge platform"
