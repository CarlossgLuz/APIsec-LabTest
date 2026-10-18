"""Authorization rules shared by document endpoints."""

from typing import TypedDict

from app.auth import User


class Document(TypedDict):
    id: int
    owner_id: int
    title: str
    content: str
    internal_notes: str


def can_read_document(user: User, document: Document) -> bool:
    return user["role"] == "admin" or user["id"] == document["owner_id"]


def can_delete_document(user: User, document: Document | None) -> bool:
    return user["role"] == "admin"
