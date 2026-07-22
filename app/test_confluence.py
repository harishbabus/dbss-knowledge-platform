from app.connectors.confluence_client import ConfluenceClient


client = ConfluenceClient()


page_id = "150710119"


# Test page details
page = client.get_page_details(
    page_id
)


print("\n========== PAGE INFO ==========")

print(page.keys())

print(
    "Title:",
    page["title"]
)


print(
    "Version:",
    page["version"]["number"]
)

print("\n===== METADATA =====")
print(page["metadata"])

print("\n===== METADATA KEYS =====")
print(page["metadata"].keys())


# Test HTML content

html_content = (
    page["body"]
    ["storage"]
    ["value"]
)


print("\n========== CONTENT ==========")

print(
    "HTML length:",
    len(html_content)
)


print(
    html_content[:500]
)


# Test attachments

attachments = client.get_attachments(
    page_id
)


print("\n========== ATTACHMENTS ==========")

print(
    "Attachment count:",
    len(
        attachments["results"]
    )
)


for attachment in attachments["results"]:

    print(
        attachment["title"]
    )