import fastapi

from .routers import predictions

app = fastapi.FastAPI()

app.include_router(predictions.router)
