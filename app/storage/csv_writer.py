import pandas as pd


def save_pages(pages, filename):

    data = [page.model_dump() for page in pages]

    df = pd.DataFrame(data)

    df.to_csv(filename, index=False)
