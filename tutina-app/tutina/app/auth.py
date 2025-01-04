import os
from typing import Annotated

import fastapi
import fastapi.security as fas
import jwt

from .dependencies import Settings, get_config

EXPECTED_AUTH_TYPE = "Bearer"
ALGORITHMS = ["HS256"]

security = fas.HTTPBearer()


def authorize(
    config: Annotated[Settings, fastapi.Depends(get_config)],
    credentials: Annotated[fas.HTTPAuthorizationCredentials, fastapi.Depends(security)],
):
    if credentials.scheme != EXPECTED_AUTH_TYPE:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported authentication type",
        )
    token_secret = config.token_secret.get_secret_value()
    try:
        return jwt.decode(credentials.credentials, token_secret, algorithms=ALGORITHMS)
    except jwt.InvalidTokenError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail=f"Unauthorized: {e}",
        ) from e
