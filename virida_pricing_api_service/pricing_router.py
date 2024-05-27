from typing import Any, Optional, List, Type, Sequence, Callable
from fastapi import APIRouter
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute
from starlette.types import ASGIApp
from starlette.responses import Response


class PricingRouter(APIRouter):
    def __init__(
        self,
        routes: Optional[List[BaseRoute]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        dependency_overrides_provider: Optional[Any] = None,
        route_class: Type[APIRoute] = APIRoute,
        default_response_class: Optional[Type[Response]] = None,
        on_startup: Optional[Sequence[Callable]] = None,
        on_shutdown: Optional[Sequence[Callable]] = None
    ) -> None:
        super().__init__(
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=APIRoute,
            default_response_class=default_response_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )

    def __call__(self, config_data: dict):
        self.config_data = config_data
        return self
