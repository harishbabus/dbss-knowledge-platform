from app.connectors.confluence_client import ConfluenceClient

client = ConfluenceClient()


response = client.get_pages(start=0, limit=5)


for page in response["results"]:

    print("====================")
    print("ID:", page["id"])
    print("TITLE:", page["title"])
    print("URL:", page["_links"]["webui"])
