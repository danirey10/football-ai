import re
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


QUARTER_METADATA = {
    "Q1": {"name": "Primer Trimestre", "months": "Ene - Mar"},
    "Q2": {"name": "Segundo Trimestre", "months": "Abr - Jun"},
    "Q3": {"name": "Tercer Trimestre", "months": "Jul - Sep"},
    "Q4": {"name": "Cuarto Trimestre", "months": "Oct - Dic"},
}


def calculate_rae(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calcula el Efecto de la Edad Relativa (RAE - Relative Age Effect).

    Recibe un DataFrame de Pandas con registros de futbolistas (debe contener
    la columna 'fecha_nacimiento'), extrae el trimestre (Q1-Q4) y calcula:
      - Frecuencia absoluta (recuento de jugadores nacidos en cada trimestre).
      - Porcentaje relativo redondeado a 2 decimales.

    Retorna un diccionario con formato:
    {
        "Q1": {"count": 142, "percentage": 40.57},
        "Q2": {"count": 98,  "percentage": 28.00},
        "Q3": {"count": 65,  "percentage": 18.57},
        "Q4": {"count": 45,  "percentage": 12.86}
    }
    """
    if df.empty:
        return {
            q: {"count": 0, "percentage": 0.0}
            for q in ["Q1", "Q2", "Q3", "Q4"]
        }

    # Asegurar conversión a tipo Datetime
    birth_dates = pd.to_datetime(df["fecha_nacimiento"], errors="coerce")
    valid_dates = birth_dates.dropna()

    if valid_dates.empty:
        return {
            q: {"count": 0, "percentage": 0.0}
            for q in ["Q1", "Q2", "Q3", "Q4"]
        }

    # Extracción del trimestre de nacimiento: 1 -> 'Q1', 2 -> 'Q2', etc.
    quarters_series = "Q" + valid_dates.dt.quarter.astype(str)

    # Cálculo de frecuencias absolutas y porcentajes asegurando indexación completa Q1-Q4
    all_quarters = ["Q1", "Q2", "Q3", "Q4"]
    counts = quarters_series.value_counts().reindex(all_quarters, fill_value=0)
    total_valid = len(valid_dates)
    percentages = (counts / total_valid * 100).round(2)

    result = {}
    for quarter in all_quarters:
        result[quarter] = {
            "count": int(counts[quarter]),
            "percentage": float(percentages[quarter]),
        }

    return result


def build_rae_payload(
    df: pd.DataFrame,
    category: str = "Canteras LaLiga / Sub-19",
    season: str = "2025/2026",
) -> Dict[str, Any]:
    """
    Enriquece el cálculo del RAE con metadatos y la estructura de lista
    requerida por el frontend Angular ('quarters').
    """
    distribution = calculate_rae(df)
    total_players = sum(item["count"] for item in distribution.values())

    quarters_list = []
    for q_id, meta in QUARTER_METADATA.items():
        data = distribution[q_id]
        quarters_list.append(
            {
                "id": q_id,
                "name": meta["name"],
                "months": meta["months"],
                "count": data["count"],
                "percentage": data["percentage"],
            }
        )

    return {
        "totalPlayers": total_players,
        "category": category,
        "season": season,
        "quarters": quarters_list,
        "distribution": distribution,
    }


async def calculate_rae_from_mongo(
    db: Any,
    category: Optional[str] = None,
    sample_size: Optional[int] = None,
    season: str = "2025/2026",
) -> Optional[Dict[str, Any]]:
    """
    Calcula el RAE directamente en el motor de MongoDB mediante una agregación nativa,
    optimizada para procesar decenas de miles de futbolistas en milisegundos sin transferir
    grandes volúmenes de datos por la red.
    """
    if db is None:
        return None

    # Verificar si la colección tiene registros
    total_docs = await db["players"].count_documents({}, limit=1)
    if total_docs == 0:
        return None

    match_filter: Dict[str, Any] = {
        "fecha_nacimiento": {"$exists": True, "$type": "string", "$regex": r"^\d{4}-\d{2}-\d{2}"}
    }

    if category and category.strip() and category != "Canteras LaLiga / Sub-19":
        cat_escaped = re.escape(category.strip())
        match_filter["$or"] = [
            {"liga": {"$regex": cat_escaped, "$options": "i"}},
            {"posicion": {"$regex": cat_escaped, "$options": "i"}},
        ]

    pipeline: List[Dict[str, Any]] = [{"$match": match_filter}]

    if sample_size is not None and sample_size > 0:
        pipeline.append({"$limit": sample_size})

    pipeline.extend([
        {
            "$project": {
                "month": {
                    "$toInt": {"$substrCP": ["$fecha_nacimiento", 5, 2]}
                }
            }
        },
        {
            "$project": {
                "quarter": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lte": ["$month", 3]}, "then": "Q1"},
                            {"case": {"$lte": ["$month", 6]}, "then": "Q2"},
                            {"case": {"$lte": ["$month", 9]}, "then": "Q3"},
                        ],
                        "default": "Q4",
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$quarter",
                "count": {"$sum": 1},
            }
        },
    ])

    cursor = db["players"].aggregate(pipeline)
    results = await cursor.to_list(length=10)

    counts: Dict[str, int] = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    for item in results:
        qid = item.get("_id")
        if qid in counts:
            counts[qid] = int(item.get("count", 0))

    total = sum(counts.values())
    if total == 0:
        return None

    distribution: Dict[str, Dict[str, float]] = {}
    quarters_list: List[Dict[str, Any]] = []

    for qid in ["Q1", "Q2", "Q3", "Q4"]:
        cnt = counts[qid]
        pct = round((cnt / total) * 100, 2)
        distribution[qid] = {"count": cnt, "percentage": pct}

        meta = QUARTER_METADATA[qid]
        quarters_list.append({
            "id": qid,
            "name": meta["name"],
            "months": meta["months"],
            "count": cnt,
            "percentage": pct,
        })

    return {
        "totalPlayers": total,
        "category": category or "Censo Global / Transfermarkt",
        "season": season,
        "quarters": quarters_list,
        "distribution": distribution,
    }


def generate_transfermarkt_mock_data(n_players: int = 350) -> pd.DataFrame:
    """
    Genera un DataFrame sintético simulando datos extraídos de Transfermarkt.
    Modela el sesgo RAE empírico real en el fútbol formativo:
      - Q1 (Ene - Mar): ~42%
      - Q2 (Abr - Jun): ~29%
      - Q3 (Jul - Sep): ~18%
      - Q4 (Oct - Dic): ~11%
    """
    np.random.seed(42)

    nombres = [
        "Lucas", "Mateo", "Hugo", "Leo", "Daniel", "Alejandro", "Pablo", "Manuel",
        "Álvaro", "Adrián", "David", "Mario", "Enzo", "Diego", "Marcos", "Iker"
    ]
    apellidos = [
        "García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez",
        "Pérez", "Gómez", "Martín", "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno"
    ]
    posiciones = [
        "Portero", "Defensa Central", "Lateral Izquierdo", "Lateral Derecho",
        "Pivote", "Mediocentro", "Extremo Izquierdo", "Extremo Derecho", "Delantero Centro"
    ]

    meses_prob = [
        0.15, 0.14, 0.13,  # Q1 (42%)
        0.11, 0.10, 0.08,  # Q2 (29%)
        0.07, 0.06, 0.05,  # Q3 (18%)
        0.04, 0.04, 0.03   # Q4 (11%)
    ]
    meses = np.random.choice(range(1, 13), size=n_players, p=meses_prob)
    dias = np.random.randint(1, 28, size=n_players)
    anios = np.random.choice([2006, 2007, 2008], size=n_players)

    fechas = [f"{y:04d}-{m:02d}-{d:02d}" for y, m, d in zip(anios, meses, dias)]
    nombres_completos = [
        f"{np.random.choice(nombres)} {np.random.choice(apellidos)}"
        for _ in range(n_players)
    ]
    posiciones_asignadas = np.random.choice(posiciones, size=n_players)

    return pd.DataFrame({
        "nombre": nombres_completos,
        "fecha_nacimiento": fechas,
        "posicion": posiciones_asignadas,
        "liga": "LaLiga EA Sports (Canteras)",
    })
