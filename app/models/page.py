from pydantic import BaseModel


class Page(BaseModel):

    id: str

    title: str

    space: str

    url: str

    version: int | None = None

    created_date: str | None = None

    updated_date: str | None = None
