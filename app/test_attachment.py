from app.connectors.confluence_client import ConfluenceClient

client = ConfluenceClient()


page_id = "97627136"


attachments = client.get_attachments(page_id)


print("===================")

print("Attachment count:", len(attachments))


for attachment in attachments:
    print(type(attachment))
    print(attachment)
