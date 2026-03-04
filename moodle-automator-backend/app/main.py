"""
Moodle Course Automator - Backend API

Punto de entrada principal de la aplicación FastAPI.
Configura CORS, rutas y eventos de ciclo de vida.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import api_router
from app.integration.moodle_client import close_moodle_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    
    - Startup: Inicialización de recursos
    - Shutdown: Limpieza de conexiones
    """
    # Startup
    print(f"🚀 Iniciando {settings.api_title}...")
    print(f"📡 Moodle URL: {settings.moodle_url}")
    print(f"🔧 Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    print("🛑 Cerrando conexiones...")
    await close_moodle_client()
    print("✅ Aplicación cerrada correctamente")


# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configurar CORS para permitir peticiones del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir router de API
app.include_router(api_router, prefix="/api")


# Rutas raíz
@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz con información básica de la API.
    """
    return {
        "name": settings.api_title,
        "version": "1.0.0",
        "description": settings.api_description,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health():
    """
    Health check básico de la API.
    """
    return {
        "status": "healthy",
        "api_version": settings.api_version,
        "debug": settings.debug
    }


# Para desarrollo local
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
