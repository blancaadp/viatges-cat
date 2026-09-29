"""Configuración central del proyecto."""

import os
from pathlib import Path

from dotenv import load_dotenv

DOMAIN = "analisi.transparenciacatalunya.cat"
DATASET_ID = "5kte-hque"
DATASET_URL = f"https://{DOMAIN}/d/{DATASET_ID}"

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REPORTS_DIR = ROOT / "reports"


def app_token() -> str | None:
    """ID de la clau API de Socrata desde .env o variables de entorno (None si no hay)."""
    load_dotenv(ROOT / ".env")
    return os.getenv("SODA_APP_TOKEN") or None


def app_secret() -> str | None:
    """Clau secreta de Socrata desde .env o variables de entorno (None si no hay)."""
    load_dotenv(ROOT / ".env")
    return os.getenv("SODA_APP_SECRET") or None
