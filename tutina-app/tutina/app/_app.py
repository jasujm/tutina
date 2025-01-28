import fastapi

from .auth import authorize
from .dependencies import preloaded_dependencies
from .routers import data, predictions

description="""
This API is part of a work-in-progress software suite for predicting and
optimizing indoor temperatures. The other main component is a Home Assistant
addon interacting with the API and producing the actual data it needs.

Interested? Well, I've got some good news and some bad news. The good news is
that the source code is available in
[GitHub](https://github.com/jasujm/tutina). The bad news is that it doesn't
really come with batteries included: The deployment only supports one user, and
currently the only known deployment is in use of the author himself.
"""

app = fastapi.FastAPI(
    title="Tutina Web Application",
    summary="A machine learning model for predicting indoor temperatures",
    description=description,
    dependencies=[fastapi.Security(authorize)],
    lifespan=preloaded_dependencies.preload,
)

app.include_router(predictions.router)
app.include_router(data.router)
