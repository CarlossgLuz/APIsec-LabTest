from pydantic import BaseModel


class PublicDocument(BaseModel):
    id: int
    owner_id: int
    title: str
    content: str
