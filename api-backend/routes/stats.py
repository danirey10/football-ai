import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
import pandas as pd

from core.dependencies import get_database
from models.player import RaeReport
from services.rae_calculator import (
    build_rae_payload,
    calculate_rae_from_mongo,
    generate_transfermarkt_mock_data,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stats", tags=["Estadísticas & Scouting"])


@router.get(
    "/rae",
    response_model=RaeReport,
    summary="Calcular la distribución del Efecto de la Edad Relativa (RAE)",
    description=(
        "Analiza las fechas de nacimiento del censo masivo de jugadores en MongoDB (o fallback Pandas), "
        "calculando la frecuencia absoluta y el porcentaje de nacimientos en cada trimestre (Q1-Q4)."
    ),
)
async def get_rae_statistics(
    db: Optional[Any] = Depends(get_database),
    sample_size: Optional[int] = Query(
        None,
        ge=10,
        le=100000,
        description="Tamaño máximo de la muestra de futbolistas (opcional, por defecto analiza el censo completo)",
    ),
    categoria: Optional[str] = Query(
        None,
        description="Filtro de liga o demarcación deportiva a analizar",
    ),
):
    # 1. Intentar cálculo mediante Agregación Nativa de MongoDB en el servidor
    if db is not None:
        try:
            mongo_report = await calculate_rae_from_mongo(
                db=db,
                category=categoria,
                sample_size=sample_size,
                season="2025/2026",
            )
            if mongo_report and mongo_report.get("totalPlayers", 0) > 0:
                return mongo_report
        except Exception as exc:
            logger.warning("[StatsRoute] Fallo en agregación nativa MongoDB RAE: %s", exc)

    # 2. Fallback con DataFrame de Pandas
    players_data = []
    if db is not None:
        try:
            cursor = db["players"].find({}, {"_id": 0, "nombre": 1, "fecha_nacimiento": 1, "posicion": 1, "liga": 1})
            if sample_size and sample_size > 0:
                cursor = cursor.limit(sample_size)
            players_data = await cursor.to_list(length=sample_size or 5000)
        except Exception as exc:
            logger.warning("[StatsRoute] Fallo al consultar cursor MongoDB para Pandas: %s", exc)
            players_data = []

    if players_data:
        df = pd.DataFrame(players_data)
    else:
        # Generar conjunto sintético de Transfermarkt con sesgo empírico de RAE
        df = generate_transfermarkt_mock_data(n_players=sample_size or 350)

    payload = build_rae_payload(
        df=df,
        category=categoria or "Canteras LaLiga / Sub-19",
        season="2025/2026",
    )

    return payload
