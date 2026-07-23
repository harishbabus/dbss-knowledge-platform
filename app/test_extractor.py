from app.connectors.confluence_client import ConfluenceClient
from app.extractors.page_extractor import PageExtractor

client = ConfluenceClient()

extractor = PageExtractor()


page_id = "150710119"


data = client.get_page_details(page_id)

import json

with open("page_debug.json", "w", encoding="utf-8") as f:

    json.dump(data, f, indent=4)

page, content = extractor.extract(data)


print("===================")

print(page)


print("===================")

print(content.plain_text[:1000])

print("Tables:", len(content.tables))

print("Hash:", content.content_hash)
