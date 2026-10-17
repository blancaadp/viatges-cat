"""Descarrega el dataset complet i el desa com a instantània en cru i immutable.

Cada execució crea data/raw/<timestamp UTC>/ amb:
  - rows.json      files tal com les retorna l'API (sense tocar)
  - metadata.json  metadades del dataset (esquema, dates d'actualització)
  - manifest.json  resum de la descàrrega (quan, quantes files, hash)
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tempfile
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
    if snapshot_dir.exists():
        raise FileExistsError(snapshot_dir)
    # S'escriu en una carpeta temporal i es reanomena al final: una descàrrega fallida
    # no deixa cap instantània a mitges.
    raw_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix=".tmp-", dir=raw_dir))
    try:
        _download(client, tmp_dir, now)
        tmp_dir.rename(snapshot_dir)
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
    log.info("Instantània desada a %s", snapshot_dir)
    return snapshot_dir


def _download(client: SodaClient | None, snapshot_dir: Path, now: datetime) -> None:

    owns_client = client is None
    client = client or SodaClient(config.DOMAIN, config.app_token(), config.app_secret())
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
    log.info("Descarregades %d files", len(rows))


def list_snapshots(raw_dir: Path = config.RAW_DIR) -> list[Path]:
    """Instantànies completes (amb manifest), de la més antiga a la més recent."""
    complete = (p for p in raw_dir.glob("*") if (p / "manifest.json").exists())
    return sorted(p for p in complete if not p.name.startswith("."))


def latest_snapshot(raw_dir: Path = config.RAW_DIR) -> Path:
    snapshots = list_snapshots(raw_dir)
    if not snapshots:
        raise FileNotFoundError(f"No hi ha instantànies a {raw_dir}. Executa `viatges ingest`.")
    return snapshots[-1]
