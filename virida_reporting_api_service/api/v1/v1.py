from fastapi import APIRouter
from .routers import reports

router = APIRouter()
router.include_router(reports.router, prefix="")