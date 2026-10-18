from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response

from app.auth import User, require_authentication
from app.data import create_documents
from app.models import PublicDocument
from app.policies import Document, can_delete_document, can_read_document


def create_app(*, include_ui: bool = True) -> FastAPI:
    application = FastAPI(
        title="APIsec", description="APIsec Lab Test", version="2.0.0"
    )
    application.state.documents = create_documents()

    @application.get("/health")
    def health():
        return {"status": "ok"}

    @application.get("/documents/{document_id}", response_model=PublicDocument)
    def get_document(
        document_id: int,
        user: Annotated[User, Depends(require_authentication)],
    ) -> Document:
        document = application.state.documents.get(document_id)
        if document is None or not can_read_document(user, document):
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    @application.delete("/documents/{document_id}", status_code=204)
    def delete_document(
        document_id: int,
        user: Annotated[User, Depends(require_authentication)],
    ) -> Response:
        document = application.state.documents.get(document_id)
        if not can_delete_document(user, document):
            raise HTTPException(status_code=403, detail="Permission denied")
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        del application.state.documents[document_id]
        return Response(status_code=204)

    return application


app = create_app()
documents = app.state.documents
