from app.connectors.confluence_client import ConfluenceClient
from app.extractors.attachment_extractor import AttachmentExtractor
from app.connectors.attachment_downloader import AttachmentDownloader


PAGE_ID = "97627136"


client = ConfluenceClient()

attachments = client.get_attachments(PAGE_ID)

extractor = AttachmentExtractor()

attachment_models = extractor.extract(
    PAGE_ID,
    attachments
)

downloader = AttachmentDownloader()


for attachment in attachment_models:

    path = downloader.download(
        attachment
    )

    print(path)