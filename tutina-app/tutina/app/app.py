import fastapi

from .auth import authorize
from .dependencies import preloaded_dependencies
from .routers import data, predictions

app = fastapi.FastAPI(
    title="Tutina",
    dependencies=[fastapi.Security(authorize)],
    lifespan=preloaded_dependencies.preload,
)

app.include_router(predictions.router)
app.include_router(data.router)
