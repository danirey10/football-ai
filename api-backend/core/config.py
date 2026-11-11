import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada y tipada de la aplicación utilizando pydantic-settings.
    Permite sobreescritura automática mediante variables de entorno o archivo .env.
    """
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base de datos MongoDB
    MONGO_URI: str = Field(
        default="mongodb://localhost:27017/scouting_db",
        description="URI de conexión asíncrona a MongoDB",
    )
    MONGO_DB_NAME: str = Field(
        default="scouting_db",
        description="Nombre de la base de datos de scouting",
    )

    @property
    def sanitized_mongo_uri(self) -> str:
        """Devuelve la URI enmascarando credenciales para registros seguros (CWE-532)."""
        import re
        if "@" in self.MONGO_URI:
            return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", self.MONGO_URI)
        return self.MONGO_URI

    # Configuración de Servidor y Entorno
    ENVIRONMENT: str = Field(default="development", description="Entorno de ejecución (development, test, production)")
    API_PORT: int = Field(default=8000, description="Puerto del servidor API")
    LOG_LEVEL: str = Field(default="INFO", description="Nivel de logging estructurado")

    # Configuración de Seguridad y CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:4200,http://127.0.0.1:4200",
        description="Lista de orígenes permitidos separados por comas",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Devuelve la lista limpia de orígenes permitidos para el middleware de CORS."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
