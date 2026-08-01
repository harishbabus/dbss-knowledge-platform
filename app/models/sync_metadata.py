from pydantic import BaseModel


class SyncMetadata(BaseModel):
    content_hash: str

    source: str

    last_synced: str
