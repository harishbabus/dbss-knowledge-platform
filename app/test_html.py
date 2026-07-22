from app.connectors.confluence_client import ConfluenceClient


client = ConfluenceClient()

page = client.get_page_details(
    "97627136"
)


html = (
    page
    .get("body", {})
    .get("storage", {})
    .get("value", "")
)


print("structured-macro:")
print(
    html.count("structured-macro")
)


print("h1:")
print(
    html.count("<h1")
)


print("strong:")
print(
    html.count("<strong")
)


print(html[:2000])