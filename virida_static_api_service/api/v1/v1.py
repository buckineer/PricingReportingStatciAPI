from fastapi import APIRouter

from .routers import static, api_key

router = APIRouter()

# route to apikey blacklist
router.include_router(api_key.router, prefix='/api_keys')
router.include_router(static.router)
