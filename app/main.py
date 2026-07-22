from app.connectors.confluence_client import ConfluenceClient


def main():

    client = ConfluenceClient()

    space = client.get_space()

    print(space)


if __name__ == "__main__":
    main()