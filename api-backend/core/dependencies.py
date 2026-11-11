from typing import Any, Optional
from fastapi import Request


async def get_database(request: Request) -> Optional[Any]:
    """
    Inyección de dependencias para obtener la instancia de base de datos MongoDB
    vinculada al estado de la aplicación FastAPI.
    """
    return getattr(request.app.state, "db", None)
