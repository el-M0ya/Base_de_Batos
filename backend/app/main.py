from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.adapters.routers.enrolments import router as enrolments_router
from app.infrastructure.persistence.connection import init_db_pool, close_db_pool

from app.adapters.routers.auth import router as auth_router
from app.adapters.routers.authorisations import router as authorisations_router
from app.adapters.routers.sites import router as sites_router
from app.infrastructure.persistence.connection import close_db_pool, init_db_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación (Startup y Shutdown).
    Aquí se inicializará y cerrará el pool de conexiones a PostgreSQL.
    """
    # --- STARTUP ---
    await init_db_pool()
    yield
    # --- SHUTDOWN ---
    await close_db_pool()


app = FastAPI(
    title="Gym Management System API",
    description="Backend API construido con FastAPI siguiendo Clean Architecture",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
from app.adapters.presentation.api.error_handlers import (
    application_error_handler,
    unexpected_error_handler,
)
from app.adapters.presentation.api.routes.catalogs import router as catalogs_router
from app.adapters.presentation.api.routes.exercises import router as exercises_router
from app.adapters.routers.authorisations import router as authorisations_router
from app.adapters.routers.sites import router as sites_router
from app.application.exceptions import ApplicationError
from app.infrastructure.persistence.connection import close_db_pool, init_db_pool


def create_app() -> FastAPI:
    """Create the configured FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db_pool()
        try:
            yield
        finally:
            await close_db_pool()

    application = FastAPI(
        title="Gym Management System API",
        description="Backend API construido con FastAPI siguiendo Clean Architecture",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(ApplicationError, application_error_handler)
    application.add_exception_handler(Exception, unexpected_error_handler)

    application.include_router(sites_router)
    application.include_router(authorisations_router)
    application.include_router(exercises_router, prefix="/api/v1")
    application.include_router(catalogs_router, prefix="/api/v1")

    @application.get("/health", tags=["Health Check"])
    async def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "message": "Gym Management Backend Service is running smoothly",
            "version": "0.1.0",
        }

    return application


# Routers of the adapter layer.
app.include_router(sites_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(authorisations_router, prefix="/api/v1")
app = create_app()
