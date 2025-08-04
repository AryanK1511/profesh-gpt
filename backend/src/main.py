from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.config import settings
from src.common.logger import logger, setup_logging
from src.common.utils.exception_handlers import register_exception_handlers
from src.common.utils.response import Response, Status
from src.common.utils.routes_logger import log_routes


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(
        title=settings.PROJECT_NAME,
        servers=[
            {
                "url": "http://127.0.0.1:8000",
                "description": "Local Development Server",
            },
        ],
        summary="Lorem Ipsum API",
        description="Lorem Ipsum API",
        version="0.1.0",
    )

    setup_logging()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    log_routes(app)

    return app


# ========== FAST API APPLICATION ==========
app: FastAPI = create_app()


# ========== HEALTH CHECK ROUTE ==========
@app.get("/health")
def health_check():
    logger.info("Server is Healthy")
    return Response.success(message="Server is Healthy", status_code=Status.OK)
