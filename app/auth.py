from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

def require_authentication(
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(security)
        ]
) -> None:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )


        raise HTTPException(
            status_code=401,
            detail="Token validation not implemented",
            headers={"WWW-Authenticate": "Bearer"},
        )
