import fastapi

from . import dependencies
from .routers import predictions

app = fastapi.FastAPI(lifespan=dependencies.lifespan)

app.include_router(predictions.router)
