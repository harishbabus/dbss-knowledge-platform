from app.connectors.confluence_client import ConfluenceClient

if __name__ == "__main__":

    client = ConfluenceClient()

    attachments = client.get_attachments("150701866")

    for a in attachments:

        print(a["filename"], "=>", a.get("media_type"))
