"""Fase 2: base de dades SQLite derivada de totes les instantànies (ADR 0003).

La base de dades es reconstrueix sencera a cada execució. Les instantànies en cru són la
font de veritat; això només n'és una vista consultable.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from viatges.changes import compare_snapshots, read_manifest
from viatges.ingest import list_snapshots
from viatges.prepare import load_manual, prepare
from viatges.profiling import load_snapshot

log = logging.getLogger(__name__)


def build_history(
    snapshots: list[Path],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Retorna (instantanies, canvis, historial_ids, darrera instantània en cru)."""
    instantanies, canvis, seen = [], [], []
    previous: pd.DataFrame | None = None
    previous_name: str | None = None
    for snapshot in snapshots:
        df, _ = load_snapshot(snapshot)
        manifest = read_manifest(snapshot)
        instantanies.append({"instantania": snapshot.name, **manifest})
        seen.append(pd.DataFrame({"id": df["id"], "instantania": snapshot.name}))
        if previous is not None:
            changes = compare_snapshots(previous, df)
            changes.insert(0, "instantania", snapshot.name)
            changes.insert(0, "instantania_anterior", previous_name)
            canvis.append(changes)
        previous, previous_name = df, snapshot.name

    names = [s.name for s in snapshots]
    order = {name: i for i, name in enumerate(names)}
    seen_df = pd.concat(seen, ignore_index=True)
    seen_df["ordre"] = seen_df["instantania"].map(order)
    historial = seen_df.groupby("id").agg(
        primera_instantania=("ordre", "min"), darrera_instantania=("ordre", "max")
    )
    historial["vigent"] = historial["darrera_instantania"] == len(names) - 1
    for col in ["primera_instantania", "darrera_instantania"]:
        historial[col] = historial[col].map(lambda i: names[i])
    historial = historial.reset_index()

    canvis_df = (
        pd.concat(canvis, ignore_index=True)
        if canvis
        else pd.DataFrame(
            columns=[
                "instantania_anterior",
                "instantania",
                "id",
                "tipus",
                "camp",
                "valor_anterior",
                "valor_nou",
            ]
        )  # fmt: skip
    )
    return pd.DataFrame(instantanies), canvis_df, historial, previous


def add_publication_delay(
    viatges: pd.DataFrame, historial: pd.DataFrame, instantanies: pd.DataFrame
) -> pd.DataFrame:
    """Afegeix `primera_aparicio` i `dies_fins_publicacio` (ADR 0003, punt 4).

    Queda buit per als ids que ja hi eren a la primera instantània (no sabem quan es van
    publicar) i per als duplicats (la seva aparició és una republicació, no la publicació).
    """
    downloaded = instantanies.set_index("instantania")["downloaded_at"]
    first = historial.set_index("id")["primera_instantania"]
    out = viatges.copy()
    out["primera_aparicio"] = pd.to_datetime(out["id"].map(first).map(downloaded), utc=True).dt.date
    known = (out["id"].map(first) != instantanies["instantania"].iloc[0]) & ~out["flag_duplicat"]
    delay = (pd.to_datetime(out["primera_aparicio"]) - pd.to_datetime(out["data_fi_iso"])).dt.days
    out["dies_fins_publicacio"] = delay.where(known).astype("Int64")
    return out


def _write(db_path: Path, tables: dict[str, pd.DataFrame]) -> None:
    """Escriu en un fitxer temporal i el reanomena: la base de dades mai queda a mitges."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    with sqlite3.connect(tmp) as con:
        for name, df in tables.items():
            df.to_sql(name, con, index=False)
        con.execute("CREATE INDEX idx_trams_id ON trams (id)")
        con.execute("CREATE INDEX idx_canvis_id ON canvis (id)")
    tmp.replace(db_path)


def build_database(raw_dir: Path, manual_dir: Path, db_path: Path) -> Path:
    snapshots = list_snapshots(raw_dir)
    if not snapshots:
        raise FileNotFoundError(f"No hi ha instantànies a {raw_dir}. Executa `viatges ingest`.")
    instantanies, canvis, historial, latest = build_history(snapshots)
    viatges, trams = prepare(latest, load_manual(manual_dir))
    viatges = add_publication_delay(viatges, historial, instantanies)
    _write(
        db_path,
        {
            "instantanies": instantanies,
            "viatges": viatges,
            "trams": trams,
            "canvis": canvis,
            "historial_ids": historial,
        },
    )
    log.info(
        "Base de dades a %s: %d instantànies, %d viatges, %d canvis",
        db_path,
        len(instantanies),
        len(viatges),
        len(canvis),
    )
    return db_path
