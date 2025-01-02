import dotenv

dotenv.load_dotenv()

import os
from typing import Annotated

import fastapi
import fastapi.security as fas
import jwt

EXPECTED_AUTH_TYPE = "Bearer"
ALGORITHMS = ["HS256"]

security = fas.HTTPBearer()


def authorize(
    credentials: Annotated[fas.HTTPAuthorizationCredentials, fastapi.Depends(security)],
):
    if credentials.scheme != EXPECTED_AUTH_TYPE:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported authentication type",
        )
    token_secret = os.environ["TUTINA_TOKEN_SECRET"]
    try:
        return jwt.decode(credentials.credentials, token_secret, algorithms=ALGORITHMS)
    except jwt.InvalidTokenError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail=f"Unauthorized: {e}",
        ) from e
