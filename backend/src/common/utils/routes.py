from typing import List

from fastapi import APIRouter, FastAPI
from src.common.logger import logger
from src.modules.auth.controllers.auth_controller import router as auth_router


def get_all_routers() -> List[APIRouter]:
    routers = []
    try:
        routers.append(auth_router)
    except ImportError as e:
        logger.warning(f"Could not import auth router: {e}")

    return routers


def register_routers(app: FastAPI) -> None:
    api_v1_router = APIRouter(prefix="/api/v1")

    routers = get_all_routers()

    for router in routers:
        api_v1_router.include_router(router)

    app.include_router(api_v1_router)
    logger.info("Registered all routers with /api/v1 prefix")


def get_registered_routes() -> List[str]:
    routes = []
    routers = get_all_routers()

    for router in routers:
        router_prefix = router.prefix or ""

        for route in router.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                full_path = f"/api/v1{router_prefix}{route.path}"
                routes.append(f"{', '.join(route.methods)} {full_path}")

    return sorted(routes)


def log_registered_routes() -> None:
    route_strings = get_registered_routes()

    if not route_strings:
        logger.warning("No routes were found in the router system")
        return

    logger.info("Routes to be registered:")
    for route in route_strings:
        logger.info(f"▸ {route}")
