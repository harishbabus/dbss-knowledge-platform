from app.connectors.confluence_client import ConfluenceClient

client = ConfluenceClient()


title = "13 - Index List"


url = f"{client.base_url}/rest/api/content"


response = client.client.get(url, params={"title": title, "spaceKey": "DPCC"})


response.raise_for_status()


data = response.json()


for page in data["results"]:

    print("===================")

    print("ID:", page["id"])

    print("Title:", page["title"])

    print("URL:", page["_links"]["webui"])
