import pandas as pd
import pytest
from fastapi.testclient import TestClient
from main import app
from services.rae_calculator import (
    build_rae_payload,
    calculate_rae,
    calculate_rae_from_mongo,
    generate_transfermarkt_mock_data,
)

client = TestClient(app)


def test_calculate_rae_with_mock_data():
    df = generate_transfermarkt_mock_data(n_players=100)
    result = calculate_rae(df)

    assert set(result.keys()) == {"Q1", "Q2", "Q3", "Q4"}

    total_count = sum(q["count"] for q in result.values())
    assert total_count == 100

    total_percentage = sum(q["percentage"] for q in result.values())
    assert 99.0 <= total_percentage <= 101.0  # Tolerancia por redondeos


def test_calculate_rae_empty_dataframe():
    df = pd.DataFrame(columns=["nombre", "fecha_nacimiento", "posicion", "liga"])
    result = calculate_rae(df)

    for q in ["Q1", "Q2", "Q3", "Q4"]:
        assert result[q]["count"] == 0
        assert result[q]["percentage"] == 0.0


def test_build_rae_payload_structure():
    df = generate_transfermarkt_mock_data(n_players=50)
    payload = build_rae_payload(df, category="Sub-19", season="2025/2026")

    assert payload["totalPlayers"] == 50
    assert payload["category"] == "Sub-19"
    assert len(payload["quarters"]) == 4
    assert "distribution" in payload
    for q in payload["quarters"]:
        assert "id" in q
        assert "name" in q
        assert "months" in q
        assert "count" in q
        assert "percentage" in q


def test_get_rae_statistics_endpoint():
    response = client.get("/api/stats/rae?sample_size=150")
    assert response.status_code == 200
    data = response.json()

    assert "totalPlayers" in data
    assert "quarters" in data
    assert len(data["quarters"]) == 4
    assert "distribution" in data

    quarter_ids = [q["id"] for q in data["quarters"]]
    assert set(quarter_ids) == {"Q1", "Q2", "Q3", "Q4"}
