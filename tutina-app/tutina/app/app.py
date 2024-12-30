import fastapi

from .routers import data, predictions

app = fastapi.FastAPI()

app.include_router(predictions.router)
app.include_router(data.router)
