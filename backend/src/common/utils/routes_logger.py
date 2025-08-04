from fastapi import FastAPI
from fastapi.routing import APIRoute

from src.common.logger import logger


def get_routes(app: FastAPI) -> list[str]:
    """Get all routes in the FastAPI application."""
    routes = []

    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(f"{', '.join(route.methods)} {route.path}")

    return sorted(routes)


def log_routes(app: FastAPI) -> None:
    """Log all mapped routes in the application."""
    route_strings = get_routes(app)

    if not route_strings:
        logger.warning("No routes were found in the application")
        return

    logger.info("Mapped Routes:")
    for route in route_strings:
        logger.info(f"▸ {route}")
