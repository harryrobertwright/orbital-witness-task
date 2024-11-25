from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.services.client import Client
from src.utils import Calculator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the lifecycle of the FastAPI application."""
    app.state.client = Client()
    app.state.calculator = Calculator()
    yield
    await app.state.client.__aexit__(None, None, None)


app = FastAPI(lifespan=lifespan)
app.include_router(router)
