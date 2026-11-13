from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.routers._errors import install_error_handlers
from app.adapters.routers.authorisations import router as authorisations_router
from app.adapters.routers.exercises import router as exercises_router
from app.adapters.routers.sites import router as sites_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación (Startup y Shutdown).
    Aquí se inicializará y cerrará el pool de conexiones a PostgreSQL.
    """
    # --- STARTUP ---
    # await init_db_pool()
    yield
    # --- SHUTDOWN ---
    # await close_db_pool()


app = FastAPI(
    title="Gym Management System API",
    description="Backend API construido con FastAPI siguiendo Clean Architecture",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# The public error contract must be active before any route is served.
install_error_handlers(app)

# Configuración de CORS (Cross-Origin Resource Sharing) para permitir conexión con el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se sustituye por las URLs del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health Check"])
def health_check():
    """
    Endpoint de verificación de estado de la API.
    """
    return {
        "status": "ok",
        "message": "Gym Management Backend Service is running smoothly",
        "version": "0.1.0",
    }


# Routers of the adapter layer.
app.include_router(sites_router)
app.include_router(authorisations_router)
app.include_router(exercises_router, prefix="/api/v1")
