import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings
from routes.players import router as players_router
from routes.stats import router as stats_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scouting_api")


async def ensure_mongo_indexes(db) -> None:
    """Asegura la creación y consistencia de los índices esenciales en MongoDB."""
    try:
        from pymongo import ASCENDING, TEXT

        await db.players.create_index([("id", ASCENDING)], unique=True, name="idx_players_id")
        await db.players.create_index([("nombre", TEXT), ("club", TEXT)], name="idx_players_text_search")
        await db.players.create_index([("nombre", ASCENDING)], name="idx_players_nombre")
        await db.players.create_index([("fecha_nacimiento", ASCENDING)], name="idx_players_fecha_nacimiento")
        await db.players.create_index([("posicion", ASCENDING)], name="idx_players_posicion")
        await db.players.create_index([("liga", ASCENDING)], name="idx_players_liga")
        logger.info("[MongoDB] Índices de rendimiento verificados con éxito.")
    except Exception as exc:
        logger.warning("[MongoDB] Advertencia al configurar índices: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización del cliente asíncrono Motor para MongoDB
    app.state.mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    app.state.db = app.state.mongo_client[settings.MONGO_DB_NAME]
    try:
        await app.state.mongo_client.admin.command("ping")
        logger.info("[MongoDB] Conexión establecida con éxito en %s", settings.sanitized_mongo_uri)
        await ensure_mongo_indexes(app.state.db)
    except Exception as exc:
        logger.warning("[MongoDB] Conexión diferida o no disponible al arrancar: %s", exc)

    yield

    # Cierre controlado de conexiones al detener la API
    if hasattr(app.state, "mongo_client") and app.state.mongo_client:
        app.state.mongo_client.close()
        logger.info("[MongoDB] Conexión cerrada de forma ordenada.")


app = FastAPI(
    title="Scouting Dashboard API",
    version="1.1.0",
    description="Motor analítico deportivo para detección del RAE (Relative Age Effect) y scouting de futbolistas.",
    lifespan=lifespan,
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers modulares
app.include_router(players_router)
app.include_router(stats_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Comprueba el estado del servicio y la conectividad con MongoDB."""
    mongo_status = "disconnected"
    if hasattr(app.state, "mongo_client") and app.state.mongo_client is not None:
        try:
            await app.state.mongo_client.admin.command("ping")
            mongo_status = "connected"
        except Exception:
            pass

    return {
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "database": mongo_status,
        "service": "scouting-dashboard-api",
    }
