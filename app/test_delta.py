from datetime import datetime, timedelta, timezone

from app.connectors.confluence_client import ConfluenceClient

client = ConfluenceClient()


modified_after = (
    datetime.now()
    -
    timedelta(days=2)
)

modified_after = (
    modified_after
    .strftime("%Y-%m-%d %H:%M")
)


pages = client.get_pages_modified_after(modified_after)


print("Modified pages:", len(pages.get("results", [])))


for page in pages.get("results", []):

    print(page["id"], page["title"])
