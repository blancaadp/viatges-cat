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
DB_PATH = DATA_DIR / "viatges.sqlite"
REPORTS_DIR = ROOT / "reports"
SITE_DIR = ROOT / "site"


def app_token() -> str | None:
    """ID de la clau API de Socrata des de .env o variables d'entorn (None si no n'hi ha)."""
    load_dotenv(ROOT / ".env")
    return os.getenv("SODA_APP_TOKEN") or None


def app_secret() -> str | None:
    """Clau secreta de Socrata des de .env o variables d'entorn (None si no n'hi ha)."""
    load_dotenv(ROOT / ".env")
    return os.getenv("SODA_APP_SECRET") or None


def turso_credentials() -> tuple[str, str]:
    """URL i token de Turso des de .env o variables d'entorn (TURSO_URL, TURSO_TOKEN)."""
    load_dotenv(ROOT / ".env")
    url, token = os.getenv("TURSO_URL"), os.getenv("TURSO_TOKEN")
    if not url or not token:
        raise RuntimeError("Falten TURSO_URL i TURSO_TOKEN al fitxer .env o a l'entorn")
    return url, token
