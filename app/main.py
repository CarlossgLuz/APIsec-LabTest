from fastapi import FastAPI, Depends, HTTPException
from app.auth import require_authentication

app = FastAPI(title="APIsec", description="APIsec Lab Test", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get(
    "documents/{document_id}",
    dependencies=[Depends(require_authentication)],
)
def get_document(document_id: int):
    raise HTTPException(
        status_code=501,
        detail="Document retrieval not implemented",
    )

