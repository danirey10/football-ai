from datetime import date
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from models.player import Player, PlayerStats

logger = logging.getLogger(__name__)

# Grupos de demarcación táctica para scouting profesional
POSITION_GROUPS: Dict[str, List[str]] = {
    "DEL": ["Delantero Centro", "Segundo Delantero", "Extremo Izquierdo", "Extremo Derecho", "Delantero", "Attack"],
    "MED": ["Centrocampista", "Pivote", "Mediapunta", "Interior Izquierdo", "Interior Derecho", "Medio", "Midfield"],
    "DEF": ["Defensa Central", "Lateral Izquierdo", "Lateral Derecho", "Defensa", "Defender"],
    "POR": ["Portero", "Arquero", "Goalkeeper"],
}

# Plantilla de referencia en memoria para tests y fallback
CURATED_PLAYERS_DATA = [
    {
        "id": 1,
        "nombre": "Pedri González",
        "fecha_nacimiento": "2002-11-25",
        "posicion": "Centrocampista",
        "liga": "LaLiga EA Sports",
        "club": "FC Barcelona",
        "pace": 79,
        "shooting": 74,
        "passing": 91,
        "dribbling": 89,
        "defending": 68,
        "physicality": 73,
        "overall": 86,
    },
    {
        "id": 2,
        "nombre": "Lamine Yamal",
        "fecha_nacimiento": "2007-07-13",
        "posicion": "Extremo Derecho",
        "liga": "LaLiga EA Sports",
        "club": "FC Barcelona",
        "pace": 89,
        "shooting": 78,
        "passing": 84,
        "dribbling": 90,
        "defending": 36,
        "physicality": 62,
        "overall": 83,
    },
    {
        "id": 3,
        "nombre": "Jude Bellingham",
        "fecha_nacimiento": "2003-06-29",
        "posicion": "Centrocampista",
        "liga": "LaLiga EA Sports",
        "club": "Real Madrid",
        "pace": 82,
        "shooting": 86,
        "passing": 85,
        "dribbling": 87,
        "defending": 78,
        "physicality": 84,
        "overall": 89,
    },
    {
        "id": 4,
        "nombre": "Kylian Mbappé",
        "fecha_nacimiento": "1998-12-20",
        "posicion": "Delantero Centro",
        "liga": "LaLiga EA Sports",
        "club": "Real Madrid",
        "pace": 97,
        "shooting": 90,
        "passing": 80,
        "dribbling": 92,
        "defending": 36,
        "physicality": 78,
        "overall": 91,
    },
    {
        "id": 5,
        "nombre": "Vinicius Jr",
        "fecha_nacimiento": "2000-07-12",
        "posicion": "Extremo Izquierdo",
        "liga": "LaLiga EA Sports",
        "club": "Real Madrid",
        "pace": 95,
        "shooting": 84,
        "passing": 81,
        "dribbling": 91,
        "defending": 32,
        "physicality": 69,
        "overall": 89,
    },
    {
        "id": 6,
        "nombre": "Erling Haaland",
        "fecha_nacimiento": "2000-07-21",
        "posicion": "Delantero Centro",
        "liga": "Premier League",
        "club": "Manchester City",
        "pace": 89,
        "shooting": 93,
        "passing": 66,
        "dribbling": 80,
        "defending": 45,
        "physicality": 88,
        "overall": 91,
    },
    {
        "id": 7,
        "nombre": "Rodri Hernández",
        "fecha_nacimiento": "1996-06-22",
        "posicion": "Pivote",
        "liga": "Premier League",
        "club": "Manchester City",
        "pace": 66,
        "shooting": 80,
        "passing": 87,
        "dribbling": 82,
        "defending": 87,
        "physicality": 85,
        "overall": 91,
    },
    {
        "id": 8,
        "nombre": "Pau Cubarsí",
        "fecha_nacimiento": "2007-01-22",
        "posicion": "Defensa Central",
        "liga": "LaLiga EA Sports",
        "club": "FC Barcelona",
        "pace": 72,
        "shooting": 40,
        "passing": 81,
        "dribbling": 72,
        "defending": 82,
        "physicality": 76,
        "overall": 80,
    },
    {
        "id": 9,
        "nombre": "Gavi",
        "fecha_nacimiento": "2004-08-05",
        "posicion": "Centrocampista",
        "liga": "LaLiga EA Sports",
        "club": "FC Barcelona",
        "pace": 78,
        "shooting": 68,
        "passing": 82,
        "dribbling": 84,
        "defending": 75,
        "physicality": 80,
        "overall": 83,
    },
    {
        "id": 10,
        "nombre": "Nico Williams",
        "fecha_nacimiento": "2002-07-12",
        "posicion": "Extremo Izquierdo",
        "liga": "LaLiga EA Sports",
        "club": "Athletic Club",
        "pace": 93,
        "shooting": 78,
        "passing": 79,
        "dribbling": 86,
        "defending": 40,
        "physicality": 74,
        "overall": 83,
    },
    {
        "id": 11,
        "nombre": "Arda Güler",
        "fecha_nacimiento": "2005-02-25",
        "posicion": "Mediapunta",
        "liga": "LaLiga EA Sports",
        "club": "Real Madrid",
        "pace": 74,
        "shooting": 76,
        "passing": 83,
        "dribbling": 84,
        "defending": 42,
        "physicality": 60,
        "overall": 79,
    },
    {
        "id": 12,
        "nombre": "Eduardo Camavinga",
        "fecha_nacimiento": "2002-11-10",
        "posicion": "Pivote",
        "liga": "LaLiga EA Sports",
        "club": "Real Madrid",
        "pace": 80,
        "shooting": 68,
        "passing": 82,
        "dribbling": 83,
        "defending": 81,
        "physicality": 82,
        "overall": 83,
    },
    {
        "id": 13,
        "nombre": "Alejandro Balde",
        "fecha_nacimiento": "2003-10-18",
        "posicion": "Lateral Izquierdo",
        "liga": "LaLiga EA Sports",
        "club": "FC Barcelona",
        "pace": 91,
        "shooting": 52,
        "passing": 74,
        "dribbling": 80,
        "defending": 76,
        "physicality": 73,
        "overall": 80,
    },
    {
        "id": 14,
        "nombre": "Dani Carvajal",
        "fecha_nacimiento": "1992-01-11",
        "posicion": "Lateral Derecho",
        "liga": "LaLiga EA Sports",
        "club": "Real Madrid",
        "pace": 81,
        "shooting": 56,
        "passing": 78,
        "dribbling": 79,
        "defending": 82,
        "physicality": 81,
        "overall": 84,
    },
    {
        "id": 15,
        "nombre": "Thibaut Courtois",
        "fecha_nacimiento": "1992-05-11",
        "posicion": "Portero",
        "liga": "LaLiga EA Sports",
        "club": "Real Madrid",
        "pace": 46,
        "shooting": 20,
        "passing": 68,
        "dribbling": 48,
        "defending": 89,
        "physicality": 80,
        "overall": 89,
    },
    {
        "id": 16,
        "nombre": "Fermín López",
        "fecha_nacimiento": "2003-05-11",
        "posicion": "Centrocampista",
        "liga": "LaLiga EA Sports",
        "club": "FC Barcelona",
        "pace": 78,
        "shooting": 80,
        "passing": 79,
        "dribbling": 81,
        "defending": 64,
        "physicality": 74,
        "overall": 79,
    },
    {
        "id": 72047,
        "nombre": "Iago Aspas",
        "fecha_nacimiento": "1987-08-01",
        "posicion": "Delantero Centro",
        "liga": "LaLiga EA Sports",
        "club": "Celta de Vigo",
        "pace": 82,
        "shooting": 85,
        "passing": 84,
        "dribbling": 86,
        "defending": 38,
        "physicality": 72,
        "overall": 83,
    },
]


def _generate_synthetic_players(start_id: int = 17, count: int = 150) -> List[Dict[str, Any]]:
    """Genera futbolistas sintéticos orientados a canteras y scouting."""
    rng = np.random.RandomState(42)

    nombres = [
        "Lucas", "Mateo", "Hugo", "Leo", "Daniel", "Alejandro", "Pablo", "Manuel",
        "Álvaro", "Adrián", "David", "Mario", "Enzo", "Diego", "Marcos", "Iker",
        "Javier", "Carlos", "Gonzalo", "Rubén", "Sergio", "Héctor", "Iván", "Samuel"
    ]
    apellidos = [
        "García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez",
        "Pérez", "Gómez", "Martín", "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno",
        "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez", "Navarro", "Torres", "Domínguez"
    ]
    posiciones = [
        "Portero", "Defensa Central", "Lateral Izquierdo", "Lateral Derecho",
        "Pivote", "Centrocampista", "Extremo Izquierdo", "Extremo Derecho", "Delantero Centro"
    ]
    clubes = [
        "Real Madrid Juvenil A", "FC Barcelona Juvenil A", "Atlético Madrileño",
        "Athletic Club Juvenil", "Valencia CF Juvenil", "Sevilla FC Juvenil",
        "Real Sociedad B", "Villarreal CF B", "Real Betis Cantera", "Celta de Vigo Juvenil"
    ]

    meses_prob = [
        0.15, 0.14, 0.13,  # Q1
        0.11, 0.10, 0.08,  # Q2
        0.07, 0.06, 0.05,  # Q3
        0.04, 0.04, 0.03   # Q4
    ]

    synthetic: List[Dict[str, Any]] = []
    for i in range(count):
        player_id = start_id + i
        nombre_completo = f"{rng.choice(nombres)} {rng.choice(apellidos)}"
        mes = int(rng.choice(range(1, 13), p=meses_prob))
        dia = int(rng.randint(1, 28))
        anio = int(rng.choice([2005, 2006, 2007, 2008]))
        fecha = f"{anio:04d}-{mes:02d}-{dia:02d}"
        pos = str(rng.choice(posiciones))
        club = str(rng.choice(clubes))

        pace, shooting, passing, dribbling, defending, physicality, overall = generate_stats_by_position(
            player_id=player_id,
            position=pos,
        )

        synthetic.append({
            "id": player_id,
            "nombre": nombre_completo,
            "fecha_nacimiento": fecha,
            "posicion": pos,
            "liga": "LaLiga EA Sports (Canteras)",
            "club": club,
            "pace": pace,
            "shooting": shooting,
            "passing": passing,
            "dribbling": dribbling,
            "defending": defending,
            "physicality": physicality,
            "overall": overall,
        })

    return synthetic


def generate_stats_by_position(player_id: int, position: str) -> Tuple[int, int, int, int, int, int, int]:
    """Genera atributos normalizados en [0, 99] adaptados a la posición de forma determinista."""
    rng = np.random.RandomState(abs(hash(f"{player_id}_{position}")) % (2**31 - 1))
    pos_lower = position.lower()

    if "delantero" in pos_lower or "ariete" in pos_lower:
        pace = rng.randint(75, 92)
        shooting = rng.randint(74, 91)
        passing = rng.randint(62, 80)
        dribbling = rng.randint(72, 88)
        defending = rng.randint(30, 50)
        physicality = rng.randint(68, 86)
    elif "extremo" in pos_lower or "punta" in pos_lower:
        pace = rng.randint(84, 96)
        shooting = rng.randint(70, 85)
        passing = rng.randint(72, 86)
        dribbling = rng.randint(80, 93)
        defending = rng.randint(32, 55)
        physicality = rng.randint(60, 78)
    elif "pivote" in pos_lower or "defensivo" in pos_lower:
        pace = rng.randint(65, 80)
        shooting = rng.randint(58, 74)
        passing = rng.randint(76, 88)
        dribbling = rng.randint(70, 82)
        defending = rng.randint(76, 90)
        physicality = rng.randint(76, 90)
    elif "centro" in pos_lower or "medio" in pos_lower or "volante" in pos_lower:
        pace = rng.randint(70, 84)
        shooting = rng.randint(68, 82)
        passing = rng.randint(78, 92)
        dribbling = rng.randint(76, 89)
        defending = rng.randint(60, 78)
        physicality = rng.randint(68, 83)
    elif "lateral" in pos_lower or "carrilero" in pos_lower:
        pace = rng.randint(82, 94)
        shooting = rng.randint(50, 68)
        passing = rng.randint(70, 82)
        dribbling = rng.randint(72, 84)
        defending = rng.randint(72, 85)
        physicality = rng.randint(70, 85)
    elif "defensa" in pos_lower or "central" in pos_lower:
        pace = rng.randint(64, 82)
        shooting = rng.randint(35, 55)
        passing = rng.randint(62, 78)
        dribbling = rng.randint(58, 74)
        defending = rng.randint(78, 92)
        physicality = rng.randint(78, 92)
    elif "portero" in pos_lower or "arquero" in pos_lower:
        pace = rng.randint(42, 60)
        shooting = rng.randint(15, 30)
        passing = rng.randint(60, 82)
        dribbling = rng.randint(42, 60)
        defending = rng.randint(80, 93)
        physicality = rng.randint(72, 88)
    else:
        pace = rng.randint(65, 85)
        shooting = rng.randint(60, 80)
        passing = rng.randint(65, 85)
        dribbling = rng.randint(65, 85)
        defending = rng.randint(55, 75)
        physicality = rng.randint(65, 85)

    pace = max(0, min(99, int(pace)))
    shooting = max(0, min(99, int(shooting)))
    passing = max(0, min(99, int(passing)))
    dribbling = max(0, min(99, int(dribbling)))
    defending = max(0, min(99, int(defending)))
    physicality = max(0, min(99, int(physicality)))

    overall = int(round(np.mean([pace, shooting, passing, dribbling, defending, physicality])))
    overall = max(0, min(99, overall))

    return pace, shooting, passing, dribbling, defending, physicality, overall


def _initialize_dataset() -> pd.DataFrame:
    """Crea y consolida el DataFrame principal de futbolistas en memoria."""
    all_players = list(CURATED_PLAYERS_DATA) + _generate_synthetic_players(
        start_id=len(CURATED_PLAYERS_DATA) + 1,
        count=150,
    )
    df = pd.DataFrame(all_players)
    return df


_PLAYERS_DF: Optional[pd.DataFrame] = None


def get_players_dataset() -> pd.DataFrame:
    global _PLAYERS_DF
    if _PLAYERS_DF is None or _PLAYERS_DF.empty:
        _PLAYERS_DF = _initialize_dataset()
    return _PLAYERS_DF


def set_players_dataset(df: pd.DataFrame) -> None:
    global _PLAYERS_DF
    _PLAYERS_DF = df.copy()


def reset_players_dataset() -> None:
    global _PLAYERS_DF
    _PLAYERS_DF = _initialize_dataset()


def _resolve_position_filter(position: Optional[str]) -> Optional[Union[List[str], str]]:
    """
    Resuelve códigos de grupo táctico ('DEL', 'MED', 'DEF', 'POR' o sus plurales)
    al conjunto completo de demarcaciones, o preserva la demarcación específica.
    """
    if not position or not str(position).strip():
        return None

    clean = str(position).strip()
    upper = clean.upper()

    if upper in ("DEL", "DELANTEROS"):
        return POSITION_GROUPS["DEL"]
    if upper in ("MED", "MEDIOS"):
        return POSITION_GROUPS["MED"]
    if upper in ("DEF", "DEFENSAS"):
        return POSITION_GROUPS["DEF"]
    if upper in ("POR", "PORTEROS"):
        return POSITION_GROUPS["POR"]

    return clean


def _search_players_in_memory(
    query: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 10,
    skip: int = 0,
    df: Optional[pd.DataFrame] = None,
) -> List[Player]:
    """Filtra el dataset de Pandas en memoria aplicando búsqueda parcial, demarcación y paginación."""
    source_df = (df if df is not None else get_players_dataset()).copy()

    if source_df.empty or "nombre" not in source_df.columns:
        return []

    # 1. Filtro por nombre o club
    if query is not None and str(query).strip() != "":
        search_term = str(query).strip()
        mask_name = source_df["nombre"].astype(str).str.contains(search_term, case=False, na=False)
        mask_club = pd.Series(False, index=source_df.index)
        if "club" in source_df.columns:
            mask_club = source_df["club"].astype(str).str.contains(search_term, case=False, na=False)
        source_df = source_df[mask_name | mask_club]

    # 2. Filtro por posición / grupo de posición
    pos_resolved = _resolve_position_filter(position)
    if pos_resolved and "posicion" in source_df.columns:
        if isinstance(pos_resolved, list):
            source_df = source_df[source_df["posicion"].isin(pos_resolved)]
        else:
            mask_pos = source_df["posicion"].astype(str).str.contains(pos_resolved, case=False, na=False)
            source_df = source_df[mask_pos]

    # Ordenar por overall descendente
    if "overall" in source_df.columns:
        source_df = source_df.sort_values(by=["overall", "id"], ascending=[False, True])

    # Paginación
    start_idx = max(0, skip)
    end_idx = start_idx + max(1, limit)
    source_df = source_df.iloc[start_idx:end_idx]

    results: List[Player] = []
    for idx, row in source_df.iterrows():
        if "id" in row and pd.notna(row["id"]):
            try:
                player_id = int(row["id"])
            except (ValueError, TypeError):
                player_id = None
        else:
            player_id = int(idx) if isinstance(idx, int) else None

        raw_birth = row.get("fecha_nacimiento")
        if isinstance(raw_birth, pd.Timestamp):
            birth_date = raw_birth.date()
        elif isinstance(raw_birth, date):
            birth_date = raw_birth
        elif isinstance(raw_birth, str) and raw_birth.strip():
            try:
                birth_date = date.fromisoformat(raw_birth.strip()[:10])
            except ValueError:
                birth_date = pd.to_datetime(raw_birth).date()
        else:
            birth_date = date(2000, 1, 1)

        player_data = {
            "id": player_id,
            "nombre": str(row["nombre"]),
            "fecha_nacimiento": birth_date,
            "posicion": str(row.get("posicion", "Desconocida")),
            "liga": str(row.get("liga", "LaLiga")),
            "club": str(row.get("club")) if pd.notna(row.get("club")) else None,
            "pace": int(row["pace"]) if "pace" in row and pd.notna(row["pace"]) else None,
            "shooting": int(row["shooting"]) if "shooting" in row and pd.notna(row["shooting"]) else None,
            "passing": int(row["passing"]) if "passing" in row and pd.notna(row["passing"]) else None,
            "dribbling": int(row["dribbling"]) if "dribbling" in row and pd.notna(row["dribbling"]) else None,
            "defending": int(row["defending"]) if "defending" in row and pd.notna(row["defending"]) else None,
            "physicality": int(row["physicality"]) if "physicality" in row and pd.notna(row["physicality"]) else None,
            "overall": int(row["overall"]) if "overall" in row and pd.notna(row["overall"]) else None,
        }

        results.append(Player(**player_data))

    return results


def _get_player_stats_in_memory(
    player_id: Union[int, str],
    df: Optional[pd.DataFrame] = None,
) -> PlayerStats:
    """Recupera los atributos de un futbolista desde el dataset en memoria."""
    source_df = df if df is not None else get_players_dataset()

    if source_df.empty:
        raise ValueError(f"Jugador con ID '{player_id}' no encontrado: dataset vacío.")

    found_row = None

    try:
        numeric_id = int(player_id)
        if "id" in source_df.columns:
            matched = source_df[source_df["id"] == numeric_id]
            if not matched.empty:
                found_row = matched.iloc[0]
    except (ValueError, TypeError):
        numeric_id = None

    if found_row is None and "id" in source_df.columns:
        matched = source_df[source_df["id"].astype(str) == str(player_id).strip()]
        if not matched.empty:
            found_row = matched.iloc[0]

    if found_row is None and "nombre" in source_df.columns:
        matched = source_df[source_df["nombre"].astype(str).str.lower() == str(player_id).strip().lower()]
        if not matched.empty:
            found_row = matched.iloc[0]

    if found_row is None:
        raise ValueError(f"Jugador con ID '{player_id}' no encontrado en el sistema.")

    resolved_id = int(found_row["id"]) if "id" in found_row and pd.notna(found_row["id"]) else (numeric_id or 1)
    nombre = str(found_row.get("nombre", f"Jugador {resolved_id}"))
    posicion = str(found_row.get("posicion", "Centrocampista"))

    required_stats = ["pace", "shooting", "passing", "defending", "physicality"]
    has_all_stats = all(stat in found_row and pd.notna(found_row[stat]) for stat in required_stats)

    if has_all_stats:
        pace = int(found_row["pace"])
        shooting = int(found_row["shooting"])
        passing = int(found_row["passing"])
        defending = int(found_row["defending"])
        physicality = int(found_row["physicality"])
        dribbling = int(found_row["dribbling"]) if "dribbling" in found_row and pd.notna(found_row["dribbling"]) else 70
        overall = int(found_row["overall"]) if "overall" in found_row and pd.notna(found_row["overall"]) else int(
            round(np.mean([pace, shooting, passing, defending, physicality]))
        )
    else:
        pace, shooting, passing, dribbling, defending, physicality, overall = generate_stats_by_position(
            player_id=resolved_id,
            position=posicion,
        )

    return PlayerStats(
        player_id=resolved_id,
        nombre=nombre,
        posicion=posicion,
        pace=max(0, min(99, pace)),
        shooting=max(0, min(99, shooting)),
        passing=max(0, min(99, passing)),
        dribbling=max(0, min(99, dribbling)),
        defending=max(0, min(99, defending)),
        physicality=max(0, min(99, physicality)),
        overall=max(0, min(99, overall)),
    )


async def search_players(
    query: Optional[str] = None,
    position: Optional[str] = None,
    max_results: int = 10,
    limit: Optional[int] = None,
    skip: int = 0,
    db: Optional[Any] = None,
    df: Optional[pd.DataFrame] = None,
) -> List[Player]:
    """
    Busca futbolistas de manera asíncrona consultando la colección MongoDB 'players'.
    Soporta filtros de grupo ('DEL', 'MED', 'DEF', 'POR'), búsqueda de texto,
    ordenación por calidad deportiva ('overall': -1) y paginación ('skip', 'limit').
    """
    effective_limit = limit if limit is not None else max_results
    effective_skip = max(0, skip)

    if df is not None:
        return _search_players_in_memory(
            query=query,
            position=position,
            limit=effective_limit,
            skip=effective_skip,
            df=df,
        )

    if db is not None:
        try:
            doc_count = await db["players"].count_documents({}, limit=1)
            if doc_count > 0:
                mongo_filter: Dict[str, Any] = {}

                # 1. Filtro por nombre o club
                if query is not None and str(query).strip():
                    escaped_query = re.escape(str(query).strip())
                    mongo_filter["$or"] = [
                        {"nombre": {"$regex": escaped_query, "$options": "i"}},
                        {"club": {"$regex": escaped_query, "$options": "i"}},
                    ]

                # 2. Filtro por demarcación o grupo táctico ('DEL', 'MED', 'DEF', 'POR')
                pos_resolved = _resolve_position_filter(position)
                if pos_resolved:
                    if isinstance(pos_resolved, list):
                        mongo_filter["posicion"] = {"$in": pos_resolved}
                    else:
                        mongo_filter["posicion"] = {"$regex": re.escape(pos_resolved), "$options": "i"}

                cursor = (
                    db["players"]
                    .find(mongo_filter, {"_id": 0})
                    .sort([("overall", -1), ("id", 1)])
                    .skip(effective_skip)
                    .limit(effective_limit)
                )

                docs = await cursor.to_list(length=effective_limit)

                results: List[Player] = []
                for doc in docs:
                    doc.pop("_id", None)
                    bdate = doc.get("fecha_nacimiento")
                    if isinstance(bdate, str):
                        try:
                            doc["fecha_nacimiento"] = date.fromisoformat(bdate[:10])
                        except ValueError:
                            doc["fecha_nacimiento"] = pd.to_datetime(bdate).date()
                    results.append(Player(**doc))

                return results

        except Exception as exc:
            logger.warning("[PlayerService] Fallback a memoria activado por error en MongoDB: %s", exc)

    return _search_players_in_memory(
        query=query,
        position=position,
        limit=effective_limit,
        skip=effective_skip,
        df=None,
    )


async def get_player_by_id(
    player_id: Union[int, str],
    db: Optional[Any] = None,
    df: Optional[pd.DataFrame] = None,
) -> Optional[Player]:
    """
    Recupera el perfil de un futbolista por su ID numérico o identificador único.
    Consulta MongoDB con fallback al dataset en memoria.
    """
    if df is not None:
        source_df = df
        try:
            num_id = int(player_id)
            matched = source_df[source_df["id"] == num_id]
            if not matched.empty:
                players = _search_players_in_memory(limit=1, df=matched)
                return players[0] if players else None
        except (ValueError, TypeError):
            pass
        return None

    if db is not None:
        try:
            conditions: List[Dict[str, Any]] = []
            try:
                num_id = int(player_id)
                conditions.append({"id": num_id})
                conditions.append({"id": str(num_id)})
            except (ValueError, TypeError):
                conditions.append({"id": str(player_id)})

            doc = await db["players"].find_one({"$or": conditions}, {"_id": 0})
            if doc:
                bdate = doc.get("fecha_nacimiento")
                if isinstance(bdate, str):
                    try:
                        doc["fecha_nacimiento"] = date.fromisoformat(bdate[:10])
                    except ValueError:
                        doc["fecha_nacimiento"] = pd.to_datetime(bdate).date()
                return Player(**doc)
        except Exception as exc:
            logger.warning("[PlayerService] Fallo al buscar jugador por ID en MongoDB: %s", exc)

    # Fallback a memoria
    try:
        num_id = int(player_id)
        source_df = get_players_dataset()
        if "id" in source_df.columns:
            matched = source_df[source_df["id"] == num_id]
            if not matched.empty:
                players = _search_players_in_memory(limit=1, df=matched)
                return players[0] if players else None
    except (ValueError, TypeError):
        pass

    return None


async def get_player_stats(
    player_id: Union[int, str],
    db: Optional[Any] = None,
    df: Optional[pd.DataFrame] = None,
) -> PlayerStats:
    """Obtiene los atributos técnicos y físicos normalizados en [0, 99]."""
    if df is not None:
        return _get_player_stats_in_memory(player_id=player_id, df=df)

    if db is not None:
        try:
            doc_count = await db["players"].count_documents({}, limit=1)
            if doc_count > 0:
                conditions: List[Dict[str, Any]] = []
                try:
                    num_id = int(player_id)
                    conditions.append({"id": num_id})
                    conditions.append({"id": str(num_id)})
                except (ValueError, TypeError):
                    conditions.append({"id": str(player_id)})

                clean_str = str(player_id).strip()
                escaped_name = re.escape(clean_str)
                conditions.append({"nombre": {"$regex": f"^{escaped_name}$", "$options": "i"}})

                doc = await db["players"].find_one({"$or": conditions}, {"_id": 0})

                if doc:
                    doc.pop("_id", None)
                    resolved_id = int(doc["id"]) if doc.get("id") is not None else 1
                    nombre = str(doc.get("nombre", f"Jugador {resolved_id}"))
                    posicion = str(doc.get("posicion", "Centrocampista"))

                    required_stats = ["pace", "shooting", "passing", "defending", "physicality"]
                    has_all = all(doc.get(stat) is not None for stat in required_stats)

                    if has_all:
                        pace = int(doc["pace"])
                        shooting = int(doc["shooting"])
                        passing = int(doc["passing"])
                        defending = int(doc["defending"])
                        physicality = int(doc["physicality"])
                        dribbling = int(doc.get("dribbling", 70))
                        overall = int(
                            doc.get(
                                "overall",
                                round(np.mean([pace, shooting, passing, defending, physicality])),
                            )
                        )
                    else:
                        pace, shooting, passing, dribbling, defending, physicality, overall = generate_stats_by_position(
                            player_id=resolved_id,
                            position=posicion,
                        )

                    return PlayerStats(
                        player_id=resolved_id,
                        nombre=nombre,
                        posicion=posicion,
                        pace=max(0, min(99, pace)),
                        shooting=max(0, min(99, shooting)),
                        passing=max(0, min(99, passing)),
                        dribbling=max(0, min(99, dribbling)),
                        defending=max(0, min(99, defending)),
                        physicality=max(0, min(99, physicality)),
                        overall=max(0, min(99, overall)),
                    )
                else:
                    # Si no está en MongoDB, verificar si está en la plantilla curada de memoria
                    try:
                        return _get_player_stats_in_memory(player_id=player_id, df=None)
                    except ValueError:
                        raise ValueError(f"Jugador con ID '{player_id}' no encontrado en el sistema.")

        except ValueError:
            raise
        except Exception as exc:
            logger.warning("[PlayerService] Fallback a memoria en get_player_stats: %s", exc)

    return _get_player_stats_in_memory(player_id=player_id, df=None)


def search_players_sync(
    query: Optional[str] = None,
    position: Optional[str] = None,
    max_results: int = 10,
    df: Optional[pd.DataFrame] = None,
) -> List[Player]:
    return _search_players_in_memory(query=query, position=position, limit=max_results, df=df)


def get_player_stats_sync(
    player_id: Union[int, str],
    df: Optional[pd.DataFrame] = None,
) -> PlayerStats:
    return _get_player_stats_in_memory(player_id=player_id, df=df)


def get_player_by_id_sync(
    player_id: Union[int, str],
    df: Optional[pd.DataFrame] = None,
) -> Optional[Player]:
    source_df = df if df is not None else get_players_dataset()
    try:
        num_id = int(player_id)
        if "id" in source_df.columns:
            matched = source_df[source_df["id"] == num_id]
            if not matched.empty:
                players = _search_players_in_memory(limit=1, df=matched)
                return players[0] if players else None
    except (ValueError, TypeError):
        pass
    return None
