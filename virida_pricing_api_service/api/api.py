from fastapi import FastAPI

from .v1.v1 import router as v1_router
from config import import_class
import os
config = import_class(os.environ['APP_SETTINGS'])

tags_metadata = [
    {
        "name": "pricing",
        "description": "Service that performs the pricing calculations."
    }
]

app = FastAPI(
    title="Virida Pricing",
    description="Virida pricing service",
    version="1.0",
    openapi_url=f"{config.API_V1_BASE_ROUTE}/openapi.json",
    openapi_tags=tags_metadata
)

app.include_router(v1_router, prefix=config.API_V1_BASE_ROUTE)


@app.get("/health")
def heartbeat():
    """
    route added to act as a probe
    """
    return {"status": "OK"}
