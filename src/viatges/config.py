"""Configuració central del projecte."""

import os
from pathlib import Path

from dotenv import load_dotenv

DOMAIN = "analisi.transparenciacatalunya.cat"
DATASET_ID = "5kte-hque"
DATASET_URL = f"https://{DOMAIN}/d/{DATASET_ID}"

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MANUAL_DIR = DATA_DIR / "manual"
REPORTS_DIR = ROOT / "reports"


def app_token() -> str | None:
    """ID de la clau API de Socrata des de .env o variables d'entorn (None si no n'hi ha)."""
    load_dotenv(ROOT / ".env")
    return os.getenv("SODA_APP_TOKEN") or None


def app_secret() -> str | None:
    """Clau secreta de Socrata des de .env o variables d'entorn (None si no n'hi ha)."""
    load_dotenv(ROOT / ".env")
    return os.getenv("SODA_APP_SECRET") or None
