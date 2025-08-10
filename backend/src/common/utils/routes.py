from typing import List

from fastapi import APIRouter, FastAPI
from src.common.logger import logger
from src.modules.agent.controllers.agent_controller import router as agent_router
from src.modules.agent.websocket.agent_websocket import router as agent_websocket_router
from src.modules.auth.controllers.auth_controller import router as auth_router
from src.modules.resume.controllers.resume_controller import (
    router as resume_router,
)


def get_all_routers() -> List[APIRouter]:
    routers = []
    try:
        routers.append(auth_router)
        routers.append(agent_router)
        routers.append(resume_router)
    except ImportError as e:
        logger.warning(f"Could not import routers: {e}")

    return routers


def get_websocket_routers() -> List[APIRouter]:
    routers = []
    try:
        routers.append(agent_websocket_router)
    except ImportError as e:
        logger.warning(f"Could not import WebSocket routers: {e}")

    return routers


def register_routers(app: FastAPI) -> None:
    api_v1_router = APIRouter(prefix="/api/v1")
    routers = get_all_routers()

    for router in routers:
        api_v1_router.include_router(router)

    app.include_router(api_v1_router)

    ws_v1_router = APIRouter(prefix="/ws/v1")
    websocket_routers = get_websocket_routers()

    for router in websocket_routers:
        ws_v1_router.include_router(router)

    app.include_router(ws_v1_router)


def get_registered_routes() -> List[str]:
    routes = []

    api_routers = get_all_routers()
    for router in api_routers:
        router_prefix = router.prefix or ""

        for route in router.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                full_path = f"/api/v1{router_prefix}{route.path}"
                routes.append(f"{', '.join(route.methods)} {full_path}")

    ws_routers = get_websocket_routers()
    for router in ws_routers:
        router_prefix = router.prefix or ""

        for route in router.routes:
            if hasattr(route, "path"):
                full_path = f"/ws/v1{router_prefix}{route.path}"
                routes.append(f"WEBSOCKET {full_path}")

    return sorted(routes)


def log_registered_routes() -> None:
    route_strings = get_registered_routes()

    if not route_strings:
        logger.warning("No routes were found in the router system")
        return

    logger.info("Routes to be registered:")
    for route in route_strings:
        logger.info(f"▸ {route}")
