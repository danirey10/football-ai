from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Player(BaseModel):
    """
    Modelo Pydantic representativo de un futbolista según la estructura
    estándar de datos deportivos (ej. Transfermarkt / Wyscout).
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, extra="forbid")

    id: Optional[int] = Field(None, description="Identificador único del futbolista", examples=[1])
    nombre: str = Field(..., description="Nombre y apellidos del jugador", examples=["Pedri González"])
    fecha_nacimiento: date = Field(..., description="Fecha de nacimiento (YYYY-MM-DD)", examples=["2002-11-25"])
    posicion: str = Field(..., description="Demarcación táctica principal", examples=["Centrocampista"])
    liga: str = Field(..., description="Liga o competición de adscripción", examples=["LaLiga"])
    club: Optional[str] = Field(None, description="Club o equipo actual", examples=["FC Barcelona"])
    pace: Optional[int] = Field(None, ge=0, le=99, description="Ritmo (0-99)", examples=[79])
    shooting: Optional[int] = Field(None, ge=0, le=99, description="Tiro (0-99)", examples=[74])
    passing: Optional[int] = Field(None, ge=0, le=99, description="Pase (0-99)", examples=[91])
    dribbling: Optional[int] = Field(None, ge=0, le=99, description="Regate (0-99)", examples=[89])
    defending: Optional[int] = Field(None, ge=0, le=99, description="Defensa (0-99)", examples=[68])
    physicality: Optional[int] = Field(None, ge=0, le=99, description="Físico (0-99)", examples=[73])
    overall: Optional[int] = Field(None, ge=0, le=99, description="Media global (0-99)", examples=[86])

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)


class PlayerStats(BaseModel):
    """
    Atributos técnicos y físicos normalizados en escala de 0 a 99
    frente a la media de referencia de su demarcación.
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, extra="forbid")

    player_id: int = Field(..., description="Identificador único del futbolista", examples=[1])
    nombre: Optional[str] = Field(None, description="Nombre del futbolista", examples=["Pedri González"])
    posicion: Optional[str] = Field(None, description="Demarcación táctica principal", examples=["Centrocampista"])
    pace: int = Field(..., ge=0, le=99, description="Ritmo / Aceleración y velocidad punta (0-99)", examples=[79])
    shooting: int = Field(..., ge=0, le=99, description="Tiro / Definición y remate (0-99)", examples=[74])
    passing: int = Field(..., ge=0, le=99, description="Pase / Visión y precisión distributiva (0-99)", examples=[91])
    dribbling: int = Field(70, ge=0, le=99, description="Regate / Control del balón y agilidad (0-99)", examples=[89])
    defending: int = Field(..., ge=0, le=99, description="Defensa / Recuperación, entradas y anticipación (0-99)", examples=[68])
    physicality: int = Field(..., ge=0, le=99, description="Físico / Potencia, fuerza y resistencia (0-99)", examples=[73])
    overall: int = Field(75, ge=0, le=99, description="Valoración general calculada (0-99)", examples=[86])

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)


class PlayerSearchResponse(BaseModel):
    """
    Contenedor opcional para respuestas de búsqueda paginadas o con metadatos.
    """
    model_config = ConfigDict(extra="forbid")
    total: int = Field(..., description="Número total de futbolistas coincidentes")
    players: List[Player] = Field(..., description="Listado de jugadores resultantes")


class QuarterMetrics(BaseModel):
    id: str = Field(..., description="Identificador del trimestre (Q1, Q2, Q3, Q4)", examples=["Q1"])
    name: str = Field(..., description="Nombre descriptivo del trimestre", examples=["Primer Trimestre"])
    months: str = Field(..., description="Rango de meses", examples=["Ene - Mar"])
    count: int = Field(..., description="Frecuencia absoluta de nacimientos", examples=[145])
    percentage: float = Field(..., description="Porcentaje relativo sobre el total", examples=[41.4])


class RaeReport(BaseModel):
    """
    Esquema de respuesta JSON para el informe RAE consumido por el frontend.
    """
    totalPlayers: int = Field(..., description="Número total de jugadores en la muestra")
    category: Optional[str] = Field(None, description="Competición o categoría analizada")
    season: Optional[str] = Field(None, description="Temporada de análisis")
    quarters: List[QuarterMetrics] = Field(..., description="Distribución por trimestre")
    distribution: dict = Field(..., description="Diccionario crudo de frecuencias y porcentajes")
