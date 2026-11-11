from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.dependencies import get_database
from models.player import Player, PlayerStats
from services.player_service import get_player_by_id, get_player_stats, search_players

router = APIRouter(prefix="/api/players", tags=["Jugadores & Scouting"])


@router.get(
    "/search",
    response_model=List[Player],
    summary="Búsqueda de futbolistas para scouting",
    description=(
        "Filtra el censo masivo de jugadores en MongoDB (con fallback a censo en memoria) "
        "mediante coincidencias parciales de texto en nombre/club y/o por posición deportiva, "
        "soportando paginación con limit y skip para censos de más de 50.000 futbolistas."
    ),
)
async def search_players_endpoint(
    db: Optional[Any] = Depends(get_database),
    query: Optional[str] = Query(
        None,
        description="Búsqueda de texto parcial en el nombre y apellidos (ej: 'Pedri', 'García')",
    ),
    q: Optional[str] = Query(
        None,
        description="Alias de 'query' para conveniencia y compatibilidad",
    ),
    position: Optional[str] = Query(
        None,
        description="Filtro de posición o demarcación táctica (ej: 'Centrocampista', 'Delantero', 'Defensa')",
    ),
    posicion: Optional[str] = Query(
        None,
        description="Alias en español para el filtro de demarcación",
    ),
    max_results: int = Query(
        10,
        ge=1,
        le=100,
        description="Número máximo de futbolistas devueltos (por defecto: 10)",
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=100,
        description="Alias de 'max_results'",
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Número de registros a omitir para paginación (offset)",
    ),
    offset: Optional[int] = Query(
        None,
        ge=0,
        description="Alias de 'skip'",
    ),
) -> List[Player]:
    effective_query = query if query is not None else q
    effective_position = position if position is not None else posicion
    effective_limit = limit if limit is not None else max_results
    effective_skip = offset if offset is not None else skip

    results = await search_players(
        query=effective_query,
        position=effective_position,
        limit=effective_limit,
        skip=effective_skip,
        db=db,
    )
    return results


@router.get(
    "/{player_id}",
    response_model=Player,
    summary="Obtener perfil completo de un futbolista por ID",
    description="Recupera la ficha deportiva y biográfica de un jugador específico por su identificador.",
)
async def get_player_by_id_endpoint(
    player_id: str,
    db: Optional[Any] = Depends(get_database),
) -> Player:
    numeric_id = int(player_id) if player_id.isdigit() else player_id
    player = await get_player_by_id(player_id=numeric_id, db=db)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Futbolista con identificador '{player_id}' no encontrado.",
        )
    return player


@router.get(
    "/{player_id}/stats",
    response_model=PlayerStats,
    summary="Atributos técnicos y físicos de un jugador",
    description=(
        "Devuelve los atributos técnicos y físicos normalizados en escala de 0 a 99 "
        "(pace, shooting, passing, dribbling, defending, physicality) "
        "consultando MongoDB con fallback a memoria."
    ),
)
async def get_player_stats_endpoint(
    player_id: str,
    db: Optional[Any] = Depends(get_database),
) -> PlayerStats:
    try:
        numeric_id = int(player_id) if player_id.isdigit() else player_id
        stats = await get_player_stats(player_id=numeric_id, db=db)
        return stats
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
