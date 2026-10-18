from copy import deepcopy

from app.policies import Document

_DOCUMENTS: dict[int, Document] = {
    1: {
        "id": 1,
        "owner_id": 1,
        "title": "Alice's document",
        "content": "Alice lab data",
        "internal_notes": "Synthetic internal review: Alice document",
    },
    2: {
        "id": 2,
        "owner_id": 2,
        "title": "Bob's document",
        "content": "Bob lab data",
        "internal_notes": "Synthetic internal review: Bob document",
    },
}


def create_documents() -> dict[int, Document]:
    return deepcopy(_DOCUMENTS)
