"""Fase 2: detecció de canvis entre dues instantànies en cru.

Es compara per `id` i a nivell de dada en cru (ADR 0003): altes, baixes i una fila per camp
modificat. La neteja no hi intervé, perquè volem saber què ha canviat el portal, no què han
canviat les nostres regles.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from viatges.profiling import load_snapshot

CHANGE_COLUMNS = ["id", "tipus", "camp", "valor_anterior", "valor_nou"]
ALTA, BAIXA, MODIFICACIO = "alta", "baixa", "modificacio"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Text sense espais als extrems; un camp buit compta igual que un camp absent."""
    out = df.set_index("id").astype("string")
    return out.apply(lambda s: s.str.strip().replace("", pd.NA))


def compare_snapshots(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """Retorna els canvis de `old` a `new` amb les columnes de `CHANGE_COLUMNS`."""
    if old["id"].duplicated().any() or new["id"].duplicated().any():
        raise ValueError("Hi ha ids duplicats: no es poden comparar les instantànies")
    a, b = _normalize(old), _normalize(new)

    altes = pd.DataFrame({"id": sorted(set(b.index) - set(a.index)), "tipus": ALTA})
    baixes = pd.DataFrame({"id": sorted(set(a.index) - set(b.index)), "tipus": BAIXA})

    common = a.index.intersection(b.index).sort_values()
    columns = sorted(set(a.columns) | set(b.columns))
    a, b = a.reindex(index=common, columns=columns), b.reindex(index=common, columns=columns)
    same = (a == b).fillna(False) | (a.isna() & b.isna())
    changed = (~same).stack()
    changed = changed[changed].index  # parells (id, camp)
    modificacions = pd.DataFrame(
        {
            "id": changed.get_level_values(0),
            "tipus": MODIFICACIO,
            "camp": changed.get_level_values(1),
            "valor_anterior": [a.at[i, c] for i, c in changed],
            "valor_nou": [b.at[i, c] for i, c in changed],
        }
    )
    frames = [f for f in (altes, baixes, modificacions) if len(f)]
    if not frames:
        return pd.DataFrame(columns=CHANGE_COLUMNS)
    return pd.concat(frames, ignore_index=True).reindex(columns=CHANGE_COLUMNS)


def _table(obj: pd.DataFrame, empty: str = "_Cap._") -> str:
    return obj.to_markdown(index=False) if len(obj) else empty


def render_changes_report(
    changes: pd.DataFrame, new: pd.DataFrame, old_info: dict, new_info: dict
) -> str:
    counts = changes["tipus"].value_counts()
    altes = new[new["id"].isin(changes.loc[changes["tipus"] == ALTA, "id"])]
    mods = changes[changes["tipus"] == MODIFICACIO].copy()
    for col in ["valor_anterior", "valor_nou"]:  # els textos llargs fan l'informe il·legible
        mods[col] = mods[col].astype("string").str.slice(0, 120).fillna("—")
    lines = [
        "# Canvis entre instantànies",
        "",
        f"- Anterior: {old_info.get('downloaded_at')} ({old_info.get('n_rows')} files)",
        f"- Nova: {new_info.get('downloaded_at')} ({new_info.get('n_rows')} files)",
        f"- Altes: **{counts.get(ALTA, 0)}** · baixes: **{counts.get(BAIXA, 0)}** · "
        f"camps modificats: **{counts.get(MODIFICACIO, 0)}**",
        "",
        "## Altes",
        "",
        _table(altes[["id", "nom", "data_inici", "destinacio", "total"]]),
        "",
        "## Baixes",
        "",
        _table(changes.loc[changes["tipus"] == BAIXA, ["id"]]),
        "",
        "## Modificacions",
        "",
        _table(mods[["id", "camp", "valor_anterior", "valor_nou"]]),
        "",
    ]
    return "\n".join(lines)


def run_changes(old_dir: Path, new_dir: Path, reports_dir: Path) -> Path:
    old, old_info = load_snapshot(old_dir)
    new, new_info = load_snapshot(new_dir)
    changes = compare_snapshots(old, new)
    out = reports_dir / "canvis" / f"{new_dir.name}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_changes_report(changes, new, old_info, new_info), encoding="utf-8")
    return out


def read_manifest(snapshot_dir: Path) -> dict:
    return json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
