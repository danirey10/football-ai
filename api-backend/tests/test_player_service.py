import pandas as pd
import pytest
from models.player import Player, PlayerStats
from services.player_service import (
    get_player_by_id,
    get_player_by_id_sync,
    get_player_stats,
    get_player_stats_sync,
    get_players_dataset,
    reset_players_dataset,
    search_players,
    search_players_sync,
    set_players_dataset,
)


@pytest.fixture(autouse=True)
def ensure_default_dataset():
    reset_players_dataset()
    yield
    reset_players_dataset()


@pytest.mark.asyncio
async def test_search_players_by_name_partial_match():
    # Coincidencia parcial con 'Pedri'
    results = await search_players(query="pedri")
    assert len(results) >= 1
    assert any("Pedri" in p.nombre for p in results)

    # Coincidencia parcial con apellido
    results_apellido = await search_players(query="bellingham")
    assert len(results_apellido) >= 1
    assert any("Bellingham" in p.nombre for p in results_apellido)


@pytest.mark.asyncio
async def test_search_players_by_position():
    results = await search_players(position="Centrocampista", max_results=20)
    assert len(results) > 0
    for p in results:
        assert "Centrocampista" in p.posicion or "medio" in p.posicion.lower() or "centro" in p.posicion.lower()


@pytest.mark.asyncio
async def test_search_players_by_name_and_position():
    results = await search_players(query="Pedri", position="Centrocampista")
    assert len(results) >= 1
    pedri = results[0]
    assert "Pedri" in pedri.nombre
    assert pedri.posicion == "Centrocampista"


@pytest.mark.asyncio
async def test_search_players_pagination_skip_and_limit():
    page_1 = await search_players(limit=5, skip=0)
    page_2 = await search_players(limit=5, skip=5)

    assert len(page_1) <= 5
    assert len(page_2) <= 5

    # Si hay suficientes jugadores, las dos páginas no deben solapar sus primeros IDs
    if len(page_1) > 0 and len(page_2) > 0:
        ids_page_1 = {p.id for p in page_1}
        ids_page_2 = {p.id for p in page_2}
        assert ids_page_1.isdisjoint(ids_page_2)


@pytest.mark.asyncio
async def test_search_players_returns_pydantic_instances():
    results = await search_players(max_results=5)
    for p in results:
        assert isinstance(p, Player)
        assert p.id is not None
        assert isinstance(p.nombre, str)
        assert p.nombre == p["nombre"]


@pytest.mark.asyncio
async def test_search_players_with_custom_dataframe():
    custom_data = [
        {"id": 101, "nombre": "Jugador Alfa", "fecha_nacimiento": "2004-01-10", "posicion": "Delantero Centro", "liga": "LaLiga"},
        {"id": 102, "nombre": "Jugador Beta", "fecha_nacimiento": "2005-03-15", "posicion": "Centrocampista", "liga": "LaLiga"},
    ]
    custom_df = pd.DataFrame(custom_data)

    results = await search_players(query="Alfa", df=custom_df)
    assert len(results) == 1
    assert results[0].nombre == "Jugador Alfa"
    assert results[0].id == 101


@pytest.mark.asyncio
async def test_get_player_stats_valid():
    stats = await get_player_stats(1)
    assert isinstance(stats, PlayerStats)
    assert stats.player_id == 1
    assert stats.nombre == "Pedri González"

    for attr in ["pace", "shooting", "passing", "dribbling", "defending", "physicality", "overall"]:
        val = getattr(stats, attr)
        assert 0 <= val <= 99
        assert stats[attr] == val


@pytest.mark.asyncio
async def test_get_player_stats_with_string_id():
    stats = await get_player_stats("1")
    assert isinstance(stats, PlayerStats)
    assert stats.player_id == 1
    assert 0 <= stats.pace <= 99


@pytest.mark.asyncio
async def test_get_player_stats_not_found():
    with pytest.raises(ValueError) as excinfo:
        await get_player_stats(999999)
    assert "no encontrado" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_player_stats_with_custom_df_dynamic_generation():
    custom_df = pd.DataFrame([
        {
            "id": 501,
            "nombre": "Promesa Juvenil",
            "fecha_nacimiento": "2008-05-20",
            "posicion": "Extremo Izquierdo",
            "liga": "Canteras",
        }
    ])
    stats = await get_player_stats(501, df=custom_df)
    assert isinstance(stats, PlayerStats)
    assert stats.player_id == 501
    assert stats.nombre == "Promesa Juvenil"
    assert 0 <= stats.pace <= 99
    assert 0 <= stats.shooting <= 99
    assert 0 <= stats.passing <= 99
    assert 0 <= stats.defending <= 99
    assert 0 <= stats.physicality <= 99


def test_sync_helpers_backward_compatibility():
    results = search_players_sync(query="Pedri", max_results=3)
    assert len(results) >= 1
    assert any("Pedri" in p.nombre for p in results)

    stats = get_player_stats_sync(1)
    assert stats.player_id == 1
    assert 0 <= stats.overall <= 99


@pytest.mark.asyncio
async def test_get_player_by_id_found_and_not_found():
    player = await get_player_by_id(1)
    assert player is not None
    assert player.id == 1
    assert "Pedri" in player.nombre

    not_found = await get_player_by_id(999999)
    assert not_found is None

    sync_player = get_player_by_id_sync(1)
    assert sync_player is not None
    assert sync_player.id == 1
