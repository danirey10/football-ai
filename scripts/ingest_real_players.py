#!/usr/bin/env python3
"""
Wrapper raíz para ejecutar el pipeline de ingesta ETL de jugadores reales.
Permite ejecutar 'python scripts/ingest_real_players.py' desde la raíz del proyecto.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_BACKEND_DIR = os.path.join(BASE_DIR, "api-backend")
if API_BACKEND_DIR not in sys.path:
    sys.path.insert(0, API_BACKEND_DIR)

from scripts.ingest_real_players import main

if __name__ == "__main__":
    main()
