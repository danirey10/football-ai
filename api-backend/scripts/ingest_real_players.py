#!/usr/bin/env python3
"""
Pipeline ETL de Ingesta de Futbolistas Reales en Activo (Transfermarkt).
Filtra estrictamente futbolistas en activo (temporadas 2024-2025),
descartando futbolistas retirados (ej. Berbatov, Marc Ziegler).
Normaliza campos al modelo Pydantic Player (atributos 0-99)
e inserta los registros por lotes en MongoDB (scouting_db.players).
"""

import argparse
import math
import os
import re
import sys
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pymongo import ASCENDING, DESCENDING, TEXT, MongoClient, ReplaceOne
from pymongo.errors import BulkWriteError, ConnectionFailure

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from models.player import Player
    from services.player_service import generate_stats_by_position
except ImportError:
    if os.path.join(CURRENT_DIR, "api-backend") not in sys.path:
        sys.path.insert(0, os.path.join(CURRENT_DIR, "api-backend"))
    from models.player import Player
    from services.player_service import generate_stats_by_position

DEFAULT_DATASET_URL = (
    "https://huggingface.co/datasets/ngeorgea/transfermarkt-player-scores/resolve/main/players.csv"
)

# Mapeo exhaustivo de demarcaciones tácticas al español
POSITION_MAPPING: Dict[str, str] = {
    "centre-forward": "Delantero Centro",
    "second striker": "Segundo Delantero",
    "left winger": "Extremo Izquierdo",
    "right winger": "Extremo Derecho",
    "attacking midfield": "Mediapunta",
    "central midfield": "Centrocampista",
    "defensive midfield": "Pivote",
    "left midfield": "Interior Izquierdo",
    "right midfield": "Interior Derecho",
    "centre-back": "Defensa Central",
    "left-back": "Lateral Izquierdo",
    "right-back": "Lateral Derecho",
    "goalkeeper": "Portero",
    # Mapeo por posición general
    "attack": "Delantero",
    "midfield": "Centrocampista",
    "defender": "Defensa",
}

# Mapeo de competiciones
COMPETITION_MAPPING: Dict[str, str] = {
    "ES1": "LaLiga EA Sports",
    "GB1": "Premier League",
    "IT1": "Serie A",
    "L1": "Bundesliga",
    "FR1": "Ligue 1",
    "PO1": "Liga Portugal",
    "NL1": "Eredivisie",
    "BE1": "Jupiler Pro League",
    "TR1": "Süper Lig",
    "GR1": "Super League Greece",
    "SC1": "Scottish Premiership",
    "DK1": "Danish Superliga",
    "RU1": "Russian Premier League",
    "UKR1": "Ukrainian Premier League",
}


def normalize_position(sub_pos: Optional[str], pos: Optional[str]) -> str:
    """Normaliza la demarcación táctica al vocabulario en español del sistema."""
    if sub_pos and isinstance(sub_pos, str) and sub_pos.strip():
        key = sub_pos.strip().lower()
        if key in POSITION_MAPPING:
            return POSITION_MAPPING[key]

    if pos and isinstance(pos, str) and pos.strip():
        key = pos.strip().lower()
        if key in POSITION_MAPPING:
            return POSITION_MAPPING[key]

    return "Centrocampista"


def normalize_competition(comp_code: Optional[str]) -> str:
    """Traduce el identificador de competición al nombre de la liga."""
    if comp_code and isinstance(comp_code, str):
        clean_code = comp_code.strip()
        if clean_code in COMPETITION_MAPPING:
            return COMPETITION_MAPPING[clean_code]
    return "Liga Profesional"


def parse_birth_date(raw_date: Any) -> Optional[date]:
    """Convierte de forma segura diversos formatos a date."""
    if raw_date is None or pd.isna(raw_date):
        return None
    if isinstance(raw_date, date) and not isinstance(raw_date, datetime):
        return raw_date
    if isinstance(raw_date, (datetime, pd.Timestamp)):
        return raw_date.date()

    date_str = str(raw_date).strip()
    if not date_str:
        return None

    date_str = date_str[:10]
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        try:
            return pd.to_datetime(date_str).date()
        except Exception:
            return None


def calculate_calibrated_stats(
    player_id: int,
    position: str,
    market_value: Optional[float] = None,
    highest_market_value: Optional[float] = None,
) -> Tuple[int, int, int, int, int, int, int]:
    """
    Calcula atributos técnicos y físicos normalizados en [0, 99],
    combinando la posición táctica con el nivel competitivo estimado.
    Considera tanto el valor de mercado actual como el pico histórico
    (highest_market_value) para reflejar fielmente la calidad de futbolistas
    consagrados y leyendas en activo (ej: Iago Aspas, Lewandowski, Modric).
    """
    base_pace, base_shoot, base_pass, base_drib, base_def, base_phys, _ = generate_stats_by_position(
        player_id=player_id,
        position=position,
    )

    mv = float(market_value) if market_value is not None and not math.isnan(market_value) else 0.0
    hmv = float(highest_market_value) if highest_market_value is not None and not math.isnan(highest_market_value) else 0.0

    # Valor de referencia deportivo ponderado
    effective_value = max(mv, hmv * 0.65)

    if effective_value >= 120_000_000:
        target_overall = 91
    elif effective_value >= 80_000_000:
        target_overall = 88
    elif effective_value >= 40_000_000:
        target_overall = 85
    elif effective_value >= 20_000_000:
        target_overall = 82
    elif effective_value >= 10_000_000:
        target_overall = 79
    elif effective_value >= 3_000_000:
        target_overall = 76
    elif effective_value >= 1_000_000:
        target_overall = 73
    else:
        target_overall = 68

    raw_mean = np.mean([base_pace, base_shoot, base_pass, base_drib, base_def, base_phys])
    delta = target_overall - raw_mean

    pace = int(max(0, min(99, round(base_pace + delta * 0.6))))
    shooting = int(max(0, min(99, round(base_shoot + delta * 0.8))))
    passing = int(max(0, min(99, round(base_pass + delta * 0.8))))
    dribbling = int(max(0, min(99, round(base_drib + delta * 0.8))))
    defending = int(max(0, min(99, round(base_def + delta * 0.8))))
    physicality = int(max(0, min(99, round(base_phys + delta * 0.6))))

    overall = int(round(np.mean([pace, shooting, passing, dribbling, defending, physicality])))
    overall = max(0, min(99, overall))

    return pace, shooting, passing, dribbling, defending, physicality, overall


def create_mongo_indexes(db) -> None:
    """Crea los índices necesarios para acelerar búsquedas, ordenación por calidad y RAE."""
    print("[ETL] Creando y optimizando índices en MongoDB...")
    db.players.create_index([("id", ASCENDING)], unique=True, name="idx_players_id")
    db.players.create_index([("overall", DESCENDING)], name="idx_players_overall")
    db.players.create_index([("posicion", ASCENDING), ("overall", DESCENDING)], name="idx_players_pos_overall")
    db.players.create_index([("nombre", TEXT), ("club", TEXT)], name="idx_players_text_search")
    db.players.create_index([("nombre", ASCENDING)], name="idx_players_nombre")
    db.players.create_index([("fecha_nacimiento", ASCENDING)], name="idx_players_fecha_nacimiento")
    db.players.create_index([("posicion", ASCENDING)], name="idx_players_posicion")
    db.players.create_index([("liga", ASCENDING)], name="idx_players_liga")
    print("[ETL] Índices creados y verificados con éxito.")


def load_and_filter_active_players(
    file_path: Optional[str] = None,
    url: Optional[str] = None,
    min_season: int = 2024,
) -> pd.DataFrame:
    """
    Carga el dataset y filtra estrictamente futbolistas en activo:
    - last_season >= min_season (por defecto 2024: temporadas 2024 y 2025).
    - Descarte de futbolistas retirados con edad > 41 años (nacidos antes de 1983).
    - Fecha de nacimiento obligatoria y válida.
    """
    target_source = file_path if file_path else (url or DEFAULT_DATASET_URL)
    print(f"[ETL] Cargando dataset desde: {target_source}")

    columns = [
        "player_id",
        "first_name",
        "last_name",
        "name",
        "last_season",
        "date_of_birth",
        "sub_position",
        "position",
        "current_club_name",
        "current_club_domestic_competition_id",
        "market_value_in_eur",
        "highest_market_value_in_eur",
    ]

    df = pd.read_csv(target_source, usecols=lambda c: c in columns)
    total_raw = len(df)
    print(f"[ETL] Total de registros leídos en bruto: {total_raw:,}")

    # 1. Filtro estricto por temporada en activo (descarta retirados históricos)
    df = df[df["last_season"] >= min_season].copy()
    print(f"[ETL] Futbolistas con ficha en activo (last_season >= {min_season}): {len(df):,}")

    # 2. Parseo y filtro de fecha de nacimiento
    df = df.dropna(subset=["date_of_birth"]).copy()
    birth_dt = pd.to_datetime(df["date_of_birth"], errors="coerce")
    # Excluir mayores de 41 años para garantizar censo en activo profesional
    df = df[birth_dt.dt.year >= 1983].copy()
    print(f"[ETL] Futbolistas activos en rango de edad profesional (< 42 años): {len(df):,}")

    return df


def run_etl_pipeline(
    mongo_uri: str,
    mongo_db_name: str,
    file_path: Optional[str] = None,
    url: Optional[str] = None,
    min_season: int = 2024,
    limit: Optional[int] = None,
    batch_size: int = 2500,
    drop_first: bool = True,
) -> int:
    """
    Ejecuta el pipeline ETL de futbolistas en activo con inserción masiva en MongoDB.
    """
    t_start = time.time()
    safe_uri = re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", mongo_uri) if "@" in mongo_uri else mongo_uri
    print(f"[ETL] Conectando a MongoDB: {safe_uri} (DB: {mongo_db_name})")
    client = MongoClient(mongo_uri)
    try:
        client.admin.command("ping")
        print("[ETL] Conexión a MongoDB establecida.")
    except ConnectionFailure as cf:
        print(f"[ETL] Error fatal de conexión a MongoDB: {cf}")
        sys.exit(1)

    db = client[mongo_db_name]

    if drop_first:
        print("[ETL] Vaciando colección previa 'players' para garantizar fuente única y limpia...")
        db.players.drop()

    create_mongo_indexes(db)

    # 1. Extracción y filtrado
    df = load_and_filter_active_players(file_path=file_path, url=url, min_season=min_season)
    if limit is not None and limit > 0:
        df = df.head(limit)
        print(f"[ETL] Procesando muestra limitada de {limit:,} futbolistas.")

    # 2. Transformación y Normalización Pydantic
    print("[ETL] Normalizando registros al modelo Pydantic Player...")
    transformed_docs: List[Dict[str, Any]] = []
    skipped = 0

    for _, row in df.iterrows():
        try:
            raw_id = row.get("player_id")
            if pd.isna(raw_id):
                skipped += 1
                continue
            player_id = int(raw_id)

            raw_name = row.get("name")
            if pd.isna(raw_name) or not str(raw_name).strip():
                fname = str(row.get("first_name", "")).strip()
                lname = str(row.get("last_name", "")).strip()
                name = f"{fname} {lname}".strip() or f"Jugador {player_id}"
            else:
                name = str(raw_name).strip()

            bdate = parse_birth_date(row.get("date_of_birth"))
            if not bdate:
                skipped += 1
                continue

            sub_pos = row.get("sub_position")
            pos = row.get("position")
            posicion = normalize_position(sub_pos, pos)

            comp_id = row.get("current_club_domestic_competition_id")
            liga = normalize_competition(comp_id)

            club_raw = row.get("current_club_name")
            club = str(club_raw).strip() if pd.notna(club_raw) and str(club_raw).strip() else "Sin club"

            mv = row.get("market_value_in_eur")
            hmv = row.get("highest_market_value_in_eur")

            pace, shoot, pas, drib, defen, phys, ovr = calculate_calibrated_stats(
                player_id=player_id,
                position=posicion,
                market_value=float(mv) if pd.notna(mv) else None,
                highest_market_value=float(hmv) if pd.notna(hmv) else None,
            )

            validated_player = Player(
                id=player_id,
                nombre=name,
                fecha_nacimiento=bdate,
                posicion=posicion,
                liga=liga,
                club=club,
                pace=pace,
                shooting=shoot,
                passing=pas,
                dribbling=drib,
                defending=defen,
                physicality=phys,
                overall=ovr,
            )

            p_dict = validated_player.model_dump()
            p_dict["fecha_nacimiento"] = bdate.isoformat()
            transformed_docs.append(p_dict)

        except Exception:
            skipped += 1
            continue

    print(f"[ETL] {len(transformed_docs):,} futbolistas normalizados listos para ingesta ({skipped} descartados).")

    # 3. Inserción por lotes en MongoDB
    total_written = 0
    total_batches = math.ceil(len(transformed_docs) / batch_size)

    for i in range(0, len(transformed_docs), batch_size):
        batch = transformed_docs[i : i + batch_size]
        operations = [
            ReplaceOne({"id": doc["id"]}, doc, upsert=True)
            for doc in batch
        ]

        try:
            res = db.players.bulk_write(operations, ordered=False)
            written = res.upserted_count + res.modified_count + res.inserted_count
            total_written += written
            batch_num = (i // batch_size) + 1
            print(f"[ETL] Lote {batch_num}/{total_batches} cargado (acumulado: {total_written:,})")
        except BulkWriteError as bwe:
            print(f"[ETL] Error parcial en lote: {bwe.details}")

    total_in_db = db.players.count_documents({})
    elapsed = time.time() - t_start
    print(
        f"[ETL] Pipeline completado en {elapsed:.2f}s! "
        f"Censo activo en scouting_db.players: {total_in_db:,} futbolistas."
    )
    client.close()
    return total_in_db


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL para ingesta masiva de futbolistas activos.")
    parser.add_argument("--url", type=str, default=DEFAULT_DATASET_URL, help="URL remota del dataset.")
    parser.add_argument("--file", type=str, default=None, help="Ruta local a players.csv.")
    parser.add_argument("--min-season", type=int, default=2024, help="Temporada mínima en activo (default: 2024).")
    parser.add_argument("--limit", type=int, default=None, help="Límite máximo de jugadores.")
    parser.add_argument("--batch-size", type=int, default=2500, help="Tamaño de lote para bulk write.")
    parser.add_argument(
        "--mongo-uri",
        type=str,
        default=os.getenv("MONGO_URI", "mongodb://localhost:27017/scouting_db"),
        help="URI de MongoDB.",
    )
    parser.add_argument(
        "--mongo-db",
        type=str,
        default=os.getenv("MONGO_DB_NAME", "scouting_db"),
        help="Nombre de la base de datos.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="No vaciar la colección antes de ingestar.",
    )

    args = parser.parse_args()

    run_etl_pipeline(
        mongo_uri=args.mongo_uri,
        mongo_db_name=args.mongo_db,
        file_path=args.file,
        url=args.url,
        min_season=args.min_season,
        limit=args.limit,
        batch_size=args.batch_size,
        drop_first=not args.keep_existing,
    )


if __name__ == "__main__":
    main()
