import fastapi

from .auth import authorize
from .routers import data, predictions

app = fastapi.FastAPI(
    title="Tutina",
    dependencies=[fastapi.Security(authorize)],
)

app.include_router(predictions.router)
app.include_router(data.router)
