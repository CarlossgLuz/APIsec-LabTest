from copy import deepcopy
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response

from app.auth import User, require_authentication
from app.main import documents
from app.policies import Document


def create_vulnerable_app() -> FastAPI:
    app = FastAPI(title="APIsec vulnerable lab")
    app.state.documents = deepcopy(documents)

    @app.get("/documents/{document_id}")
    def get_document(
        document_id: int,
        user: Annotated[User, Depends(require_authentication)],
    ) -> Document:
        document = app.state.documents.get(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    @app.delete("/documents/{document_id}", status_code=204)
    def delete_document(
        document_id: int,
        user: Annotated[User, Depends(require_authentication)],
    ) -> Response:
        if document_id not in app.state.documents:
            raise HTTPException(status_code=404, detail="Document not found")
        del app.state.documents[document_id]
        return Response(status_code=204)

    return app
