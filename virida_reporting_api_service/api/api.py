import os
from fastapi import FastAPI

from .v1.v1 import router as v1_router
from config import config

tags_metadata = [
    {
        "name": "reports",
        "description": "Reports related operations"
    }
]

app = FastAPI(
    title="Virida Reporting",
    description="Virida reporting service",
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
