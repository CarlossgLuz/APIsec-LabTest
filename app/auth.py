from typing import Annotated, TypedDict

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

class User(TypedDict):
    id: int
    role: str


DEMO_USERS: dict[str, User] = {
    "alice-token": {"id": 1, "role": "user"},
    "bob-token": {"id": 2, "role": "user"},
    "admin-token": {"id": 3, "role": "admin"},
}

security = HTTPBearer(auto_error=False)


def require_authentication(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = DEMO_USERS.get(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user.copy()
