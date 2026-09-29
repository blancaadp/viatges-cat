"""Descarga el dataset completo y lo guarda como instantánea cruda e inmutable.

Cada ejecución crea data/raw/<timestamp UTC>/ con:
  - rows.json      filas tal como las devuelve la API (sin tocar)
  - metadata.json  metadatos del dataset (esquema, fechas de actualización)
  - manifest.json  resumen de la descarga (cuándo, cuántas filas, hash)
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from viatges import config
from viatges.soda import SodaClient

log = logging.getLogger(__name__)


def _write_json(path: Path, obj: object) -> bytes:
    data = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    path.write_bytes(data)
    return data


def run_ingest(client: SodaClient | None = None, raw_dir: Path = config.RAW_DIR) -> Path:
    now = datetime.now(UTC)
    snapshot_dir = raw_dir / now.strftime("%Y-%m-%dT%H%M%SZ")
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    owns_client = client is None
    client = client or SodaClient(config.DOMAIN, config.app_token())
    try:
        metadata = client.metadata(config.DATASET_ID)
        rows = client.fetch_all(config.DATASET_ID)
    finally:
        if owns_client:
            client.__exit__()

    raw_bytes = _write_json(snapshot_dir / "rows.json", rows)
    _write_json(snapshot_dir / "metadata.json", metadata)

    rows_updated_at = metadata.get("rowsUpdatedAt")
    manifest = {
        "dataset_id": config.DATASET_ID,
        "source": config.DATASET_URL,
        "downloaded_at": now.isoformat(),
        "n_rows": len(rows),
        "rows_updated_at": (
            datetime.fromtimestamp(rows_updated_at, UTC).isoformat() if rows_updated_at else None
        ),
        "sha256_rows": hashlib.sha256(raw_bytes).hexdigest(),
    }
    _write_json(snapshot_dir / "manifest.json", manifest)
    log.info("Instantánea guardada en %s (%d filas)", snapshot_dir, len(rows))
    return snapshot_dir


def latest_snapshot(raw_dir: Path = config.RAW_DIR) -> Path:
    snapshots = sorted(p for p in raw_dir.glob("*") if (p / "manifest.json").exists())
    if not snapshots:
        raise FileNotFoundError(f"No hay instantáneas en {raw_dir}. Ejecuta `viatges ingest`.")
    return snapshots[-1]
