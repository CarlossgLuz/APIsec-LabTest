from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response

from app.auth import User, require_authentication
from app.policies import Document, can_delete_document, can_read_document

app = FastAPI(title="APIsec", description="APIsec Lab Test", version="1.0.0")

# Synthetic, process-local data. Restarting the server resets this store.
documents: dict[int, Document] = {
    1: {"id": 1, "owner_id": 1, "title": "Alice's document", "content": "Alice lab data"},
    2: {"id": 2, "owner_id": 2, "title": "Bob's document", "content": "Bob lab data"},
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents/{document_id}")
def get_document(
    document_id: int,
    user: Annotated[User, Depends(require_authentication)],
) -> Document:
    document = documents.get(document_id)
    if document is None or not can_read_document(user, document):
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    user: Annotated[User, Depends(require_authentication)],
) -> Response:
    document = documents.get(document_id)
    # Deny ordinary users consistently, including for nonexistent IDs.
    if not can_delete_document(user, document):
        raise HTTPException(status_code=403, detail="Permission denied")
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    del documents[document_id]
    return Response(status_code=204)
