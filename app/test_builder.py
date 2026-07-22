from app.connectors.confluence_client import ConfluenceClient

from app.extractors.page_extractor import PageExtractor
from app.extractors.attachment_extractor import AttachmentExtractor

from app.builders.knowledge_builder import KnowledgeBuilder

from app.storage.knowledge_repository import KnowledgeRepository
from app.storage.attachment_repository import AttachmentRepository



client = ConfluenceClient()

page_extractor = PageExtractor()

attachment_extractor = AttachmentExtractor()

builder = KnowledgeBuilder()

knowledge_repo = KnowledgeRepository()

attachment_repo = AttachmentRepository()



page_id = "97627136"



page_data = client.get_page_details(
    page_id
)


page, content = (
    page_extractor
    .extract(page_data)
)



attachment_data = (
    client
    .get_attachments(
        page_id
    )
)



attachments = (
    attachment_extractor
    .extract(
        page_id,
        attachment_data
    )
)



print(
    "Attachments extracted:",
    len(attachments)
)



attachment_repo.save_many(
    attachments
)



knowledge_page = (
    builder
    .build(
        page_data,
        content.model_dump(),
        [
            a.model_dump()
            for a in attachments
        ]
    )
)



knowledge_repo.save(
    knowledge_page
)



print(
    "Knowledge pages:",
    knowledge_repo.count()
)