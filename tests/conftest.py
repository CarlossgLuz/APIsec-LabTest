from copy import deepcopy

import pytest

from app.main import documents


@pytest.fixture(autouse=True)
def restore_documents():
    """Restore the in-memory store even when a deletion test fails."""
    snapshot = deepcopy(documents)
    yield
    documents.clear()
    documents.update(snapshot)
