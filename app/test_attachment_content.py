from app.connectors.confluence_client import ConfluenceClient
from app.extractors.attachment_extractor import AttachmentExtractor
from app.extractors.attachment_content_extractor import AttachmentContentExtractor
from app.connectors.attachment_downloader import AttachmentDownloader



page_id = "97627136"


client = ConfluenceClient()


raw = client.get_attachments(
    page_id
)


attachments = (
    AttachmentExtractor()
    .extract(
        page_id,
        raw
    )
)


downloader = AttachmentDownloader()

extractor = AttachmentContentExtractor()



for attachment in attachments:


    downloader.download(
        attachment
    )


    content = extractor.extract(
        attachment
    )

    if content:
        print(
            content["text"][:500]
        )
    else:
        print("No Extractable Content")


    print(
        "\n================="
    )

    print(
        attachment.filename
    )

    print(
        content
        if content
        else "No content"
    )