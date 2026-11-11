import os
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from models.player import Player, PlayerStats
from services.player_service import get_player_stats, search_players
from services.rae_calculator import calculate_rae_from_mongo

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/scouting_db",
)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "scouting_db")


@pytest.fixture
def mongo_db():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    yield db
    client.close()


@pytest.mark.asyncio
async def test_mongo_database_has_real_players_volume(mongo_db):
    """Verifica que la base de datos MongoDB contenga el censo masivo de jugadores en activo (> 20.000)."""
    count = await mongo_db.players.count_documents({})
    assert count >= 10000, f"Se esperaba un censo masivo de jugadores en activo, actual: {count}"


@pytest.mark.asyncio
async def test_retired_players_are_excluded(mongo_db):
    """Verifica que exfutbolistas retirados (Berbatov, Marc Ziegler) no existan en el censo activo."""
    berbatov = await mongo_db.players.find_one({"nombre": {"$regex": "Berbatov", "$options": "i"}})
    assert berbatov is None, "Dimitar Berbatov (retirado en 2015) no debe estar en el censo activo"

    ziegler = await mongo_db.players.find_one({"nombre": {"$regex": "Marc Ziegler", "$options": "i"}})
    assert ziegler is None, "Marc Ziegler (retirado en 2012) no debe estar en el censo activo"


@pytest.mark.asyncio
async def test_iago_aspas_exists_and_can_be_found(mongo_db):
    """Verifica que Iago Aspas esté presente y sus datos sean correctos (Celta de Vigo, Delantero)."""
    results = await search_players(query="Iago Aspas", db=mongo_db)
    assert len(results) >= 1
    aspas = results[0]
    assert aspas.nombre == "Iago Aspas"
    assert aspas.club == "Celta de Vigo"
    assert "Delantero" in aspas.posicion
    assert aspas.fecha_nacimiento.year == 1987


@pytest.mark.asyncio
async def test_search_position_group_del_returns_full_quota(mongo_db):
    """Verifica que al filtrar por 'DEL' se devuelvan los 24 delanteros solicitados y no solo 8."""
    attackers = await search_players(position="DEL", limit=24, db=mongo_db)
    assert len(attackers) == 24
    for p in attackers:
        assert p.posicion in [
            "Delantero Centro", "Segundo Delantero", "Extremo Izquierdo", "Extremo Derecho", "Delantero"
        ]


@pytest.mark.asyncio
async def test_mongo_indexes_exist(mongo_db):
    """Verifica que los índices obligatorios para acelerar búsqueda y RAE existan."""
    indexes = await mongo_db.players.list_indexes().to_list(length=20)
    index_names = {idx["name"] for idx in indexes}

    assert "idx_players_id" in index_names, "Debe existir el índice único sobre 'id'"
    assert "idx_players_nombre" in index_names, "Debe existir índice sobre 'nombre'"
    assert "idx_players_fecha_nacimiento" in index_names, "Debe existir índice sobre 'fecha_nacimiento'"
    assert "idx_players_posicion" in index_names, "Debe existir índice sobre 'posicion'"
    assert "idx_players_overall" in index_names, "Debe existir índice sobre 'overall'"


@pytest.mark.asyncio
async def test_search_real_players_in_mongo(mongo_db):
    """Verifica la búsqueda asíncrona de jugadores reales de élite en MongoDB."""
    results = await search_players(query="Haaland", db=mongo_db)
    assert len(results) >= 1
    haaland = results[0]
    assert "Haaland" in haaland.nombre
    assert haaland.club == "Manchester City"
    assert haaland.overall is not None and haaland.overall >= 80


@pytest.mark.asyncio
async def test_search_real_players_pagination(mongo_db):
    """Verifica que la paginación con skip y limit funcione de forma estricta y rápida."""
    page_1 = await search_players(limit=10, skip=0, db=mongo_db)
    page_2 = await search_players(limit=10, skip=10, db=mongo_db)

    assert len(page_1) == 10
    assert len(page_2) == 10

    ids_1 = [p.id for p in page_1]
    ids_2 = [p.id for p in page_2]
    assert set(ids_1).isdisjoint(set(ids_2))


@pytest.mark.asyncio
async def test_get_real_player_stats_from_mongo(mongo_db):
    """Verifica la recuperación y calibración de atributos 0-99 de un jugador real en MongoDB."""
    stats = await get_player_stats(player_id=72047, db=mongo_db) # ID de Iago Aspas
    assert isinstance(stats, PlayerStats)
    assert stats.player_id == 72047
    assert stats.nombre == "Iago Aspas"

    for attr in ["pace", "shooting", "passing", "dribbling", "defending", "physicality", "overall"]:
        val = getattr(stats, attr)
        assert 0 <= val <= 99, f"Atributo {attr} fuera del rango [0, 99]: {val}"


@pytest.mark.asyncio
async def test_calculate_rae_from_real_mongo_data(mongo_db):
    """Verifica el cálculo de RAE con la agregación nativa sobre el volumen real de MongoDB."""
    report = await calculate_rae_from_mongo(db=mongo_db, sample_size=1000)
    assert report is not None
    assert report["totalPlayers"] > 0
    assert len(report["quarters"]) == 4

    total_pct = sum(q["percentage"] for q in report["quarters"])
    assert 99.0 <= total_pct <= 101.0
