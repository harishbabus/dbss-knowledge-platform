from app.connectors.confluence_client import ConfluenceClient
from app.extractors.page_extractor import PageExtractor

from app.storage.page_repository import PageRepository
from app.storage.content_repository import ContentRepository


client = ConfluenceClient()

extractor = PageExtractor()


page_id = "150710119"


data = client.get_page_details(
    page_id
)


page, content = extractor.extract(
    data
)


page_repo = PageRepository()

content_repo = ContentRepository()


page_repo.save_page(
    page
)


content_repo.save(
    content
)


print(
    "Pages:",
    page_repo.count()
)


print(
    "Contents:",
    content_repo.count()
)