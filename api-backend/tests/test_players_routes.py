import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_search_players_endpoint_default():
    response = client.get("/api/players/search")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    if data:
        first = data[0]
        assert "id" in first
        assert "nombre" in first
        assert "posicion" in first
        assert "fecha_nacimiento" in first


def test_search_players_endpoint_query():
    response = client.get("/api/players/search?query=Pedri")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Pedri" in p["nombre"] for p in data)


def test_search_players_endpoint_q_alias():
    response = client.get("/api/players/search?q=Mbappé")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Mbappé" in p["nombre"] for p in data)


def test_search_players_endpoint_position():
    response = client.get("/api/players/search?position=Delantero")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for p in data:
        assert "delantero" in p["posicion"].lower() or "ariete" in p["posicion"].lower()


def test_search_players_endpoint_posicion_alias():
    response = client.get("/api/players/search?posicion=Centrocampista&max_results=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5
    for p in data:
        assert "centrocampista" in p["posicion"].lower() or "medio" in p["posicion"].lower()


def test_search_players_endpoint_limit():
    response = client.get("/api/players/search?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3


def test_search_players_endpoint_pagination_skip():
    resp_page_1 = client.get("/api/players/search?limit=3&skip=0")
    resp_page_2 = client.get("/api/players/search?limit=3&skip=3")
    assert resp_page_1.status_code == 200
    assert resp_page_2.status_code == 200

    page_1 = resp_page_1.json()
    page_2 = resp_page_2.json()

    if len(page_1) > 0 and len(page_2) > 0:
        ids_1 = {p["id"] for p in page_1}
        ids_2 = {p["id"] for p in page_2}
        assert ids_1.isdisjoint(ids_2)


def test_get_player_stats_endpoint_success():
    response = client.get("/api/players/1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 1
    assert "Pedri" in data["nombre"]

    for stat in ["pace", "shooting", "passing", "defending", "physicality", "dribbling", "overall"]:
        assert stat in data
        assert isinstance(data[stat], int)
        assert 0 <= data[stat] <= 99


def test_get_player_stats_endpoint_not_found():
    response = client.get("/api/players/99999999/stats")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error
    assert "no encontrado" in error["detail"]


def test_get_player_by_id_endpoint_success():
    response = client.get("/api/players/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "Pedri" in data["nombre"]
    assert data["posicion"] == "Centrocampista"


def test_get_player_by_id_endpoint_not_found():
    response = client.get("/api/players/99999999")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error
    assert "no encontrado" in error["detail"]


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "database" in data
    assert data["service"] == "scouting-dashboard-api"
