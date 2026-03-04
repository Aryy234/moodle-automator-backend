"""
Global Configuration Management

Gestión centralizada de variables de entorno y configuración de la aplicación.
Utiliza pydantic-settings para validación y carga automática desde .env
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.
    
    Las variables se cargan automáticamente desde el archivo .env
    o pueden ser definidas como variables de entorno del sistema.
    """
    
    # Moodle Configuration
    moodle_url: str
    moodle_token: str
    
    # Application Settings
    debug: bool = False
    api_version: str = "v1"
    
    # API Settings
    api_title: str = "Moodle Course Automator API"
    api_description: str = "API para la automatización de duplicación y personalización de cursos en Moodle"
    
    # CORS Settings (para desarrollo local y red local)
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.100.218:5173",
    ]
    
    # Moodle API Endpoints (constantes derivadas)
    @property
    def moodle_webservice_url(self) -> str:
        """URL completa del endpoint de Web Services de Moodle"""
        base = self.moodle_url.rstrip("/")
        return f"{base}/webservice/rest/server.php"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Obtiene la instancia de configuración (singleton con caché).
    
    Returns:
        Settings: Instancia única de configuración
    """
    return Settings()


# Alias para acceso directo
settings = get_settings()
