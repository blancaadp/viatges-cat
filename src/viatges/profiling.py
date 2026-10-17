"""Fase 0: inventario de calidad de los datos crudos.

Aquí NO se limpia nada. Solo se mide y se documenta lo que hay, para decidir
después las reglas de limpieza con datos en la mano.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from viatges.schema import AMOUNT_COLUMNS, COST_COLUMNS, DATE_COLUMNS, field_mapping

# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------


def load_snapshot(snapshot_dir: Path) -> tuple[pd.DataFrame, dict]:
    rows = json.loads((snapshot_dir / "rows.json").read_text(encoding="utf-8"))
    metadata = json.loads((snapshot_dir / "metadata.json").read_text(encoding="utf-8"))
    manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    mapping, unexpected, missing = field_mapping(metadata)
    df = pd.DataFrame(rows).rename(columns=mapping)
    for col in missing:  # así el resto del perfilado no falla
        df[col] = pd.NA
    info = {**manifest, "unexpected_columns": unexpected, "missing_columns": missing}
    return df, info


# ---------------------------------------------------------------------------
# Parsers tolerantes (devuelven valor + máscara de fallos, nunca lanzan)
# ---------------------------------------------------------------------------


def _as_text(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip()


def parse_amount(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    txt = _as_text(s)
    has_comma = txt.str.contains(",", na=False)
    # "1.234,56" o "2,05" -> formato con punto decimal
    txt = txt.mask(has_comma, txt.str.replace(".", "", regex=False).str.replace(",", "."))
    num = pd.to_numeric(txt, errors="coerce")
    failed = num.isna() & txt.notna() & (txt != "")
    return num, failed


def parse_date(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    txt = _as_text(s)
    iso = pd.to_datetime(txt.str[:10], format="%Y-%m-%d", errors="coerce")
    dmy = pd.to_datetime(txt, format="%d/%m/%Y", errors="coerce")
    out = iso.fillna(dmy)
    failed = out.isna() & txt.notna() & (txt != "")
    return out, failed


# ---------------------------------------------------------------------------
# Valores de relleno ("cap", "sense", "-", "*"...)
# ---------------------------------------------------------------------------

_ONLY_PUNCT = re.compile(r"^[\W_]*$")
_PLACEHOLDER_WORDS = {
    "0", "0.00", "0,00", "o,oo", "no", "x", "cap", "sense", "res", "n/a", "cao",
    "no n'hi ha", "no hi ha", "no té comitiva", "sense comitiva", "no hi ha comitiva",
    "sense observacions", "cap observació", "no hi ha observacions",
    "no hi ha cap observació", "no hi cap observació", "sense obaservacions",
}  # fmt: skip


def placeholder_mask(s: pd.Series) -> pd.Series:
    """True si el valor está vacío o es un texto de relleno. Heurística: revisar a mano."""
    norm = _as_text(s).str.lower().str.rstrip(".").str.strip()
    is_placeholder = norm.isna() | norm.str.match(_ONLY_PUNCT) | norm.isin(_PLACEHOLDER_WORDS)
    return is_placeholder.fillna(True).astype(bool)


# ---------------------------------------------------------------------------
# Destinos
# ---------------------------------------------------------------------------

_DEST_RE = re.compile(r"^\s*(?P<ciutat>[^()]+?)\s*(?:\((?P<pais>[^)]*)\))?\s*$")


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def split_destinations(df: pd.DataFrame) -> pd.DataFrame:
    """Un registro por tramo de destino: 'A (X) / B (Y)' -> dos filas."""
    parts = df[["id", "destinacio"]].copy()
    parts["tram"] = _as_text(parts["destinacio"]).str.split("/")
    parts = parts.explode("tram")
    parts["tram"] = parts["tram"].str.strip()
    parts = parts[parts["tram"].notna() & (parts["tram"] != "")]
    extracted = parts["tram"].str.extract(_DEST_RE)
    return parts.assign(ciutat=extracted["ciutat"], pais=extracted["pais"])


def city_variant_groups(trams: pd.DataFrame, prefix_len: int = 5) -> pd.DataFrame:
    """Agrupa grafías que probablemente son la misma ciudad (heurística por prefijo)."""
    t = trams.dropna(subset=["ciutat"]).copy()
    t["clau"] = t["ciutat"].map(lambda c: re.sub(r"[^a-z]", "", strip_accents(c))[:prefix_len])
    groups = (
        t.groupby("clau")
        .agg(
            variants=("ciutat", lambda s: sorted(set(s))),
            n_variants=("ciutat", "nunique"),
            n_registres=("id", "nunique"),
        )
        .query("n_variants > 1")
        .sort_values(["n_variants", "n_registres"], ascending=False)
    )
    groups["variants"] = groups["variants"].map(" | ".join)
    return groups


# ---------------------------------------------------------------------------
# Inventario
# ---------------------------------------------------------------------------


def build_inventory(df: pd.DataFrame) -> dict:
    inv: dict = {"n_rows": len(df)}
    work = df.copy()

    # Importes
    amount_failures = {}
    for col in AMOUNT_COLUMNS:
        work[col], failed = parse_amount(df[col])
        amount_failures[col] = df.loc[failed, col].astype(str).value_counts().head(10).to_dict()
    inv["amount_parse_failures"] = amount_failures

    # Fechas
    date_failures = {}
    for col in DATE_COLUMNS:
        work[col], failed = parse_date(df[col])
        date_failures[col] = df.loc[failed, col].astype(str).value_counts().head(10).to_dict()
    inv["date_parse_failures"] = date_failures

    dur = (work["data_fi"] - work["data_inici"]).dt.days + 1
    inv["date_range"] = (work["data_inici"].min(), work["data_inici"].max())
    inv["end_before_start"] = work.loc[dur < 1, ["id", "data_inici", "data_fi"]]
    inv["duration_describe"] = dur.describe()
    inv["long_trips"] = work.loc[dur > 21, ["id", "destinacio", "data_inici", "data_fi"]]
    inv["future_dates"] = int((work["data_inici"] > pd.Timestamp.now()).sum())

    # Totales
    comp = work[COST_COLUMNS].sum(axis=1, min_count=1)
    diff = work["total"] - comp
    mismatch = diff.abs() > 0.01
    inv["total_missing"] = int(work["total"].isna().sum())
    inv["total_mismatch"] = work.loc[mismatch, ["id", *COST_COLUMNS, "total"]].assign(
        diferencia=diff[mismatch].round(2)
    )
    inv["total_zero"] = int((work["total"] == 0).sum())
    inv["negative_amounts"] = int((work[AMOUNT_COLUMNS] < 0).sum().sum())
    inv["amounts_describe"] = work[AMOUNT_COLUMNS].describe().T

    # Mismo importe en registros distintos (posible gasto compartido o duplicado)
    shared = []
    for col in COST_COLUMNS:
        vals = work.loc[work[col] > 0, ["id", col]]
        repeated = vals[vals.duplicated(col, keep=False)]
        for value, grp in repeated.groupby(col):
            shared.append({"columna": col, "import": value, "ids": ", ".join(grp["id"])})
    inv["shared_amounts"] = pd.DataFrame(shared)

    # Duplicados
    inv["duplicated_ids"] = int(df["id"].duplicated().sum())
    key = ["nom", "data_inici", "destinacio"]
    inv["duplicated_trips"] = df.loc[df.duplicated(key, keep=False), ["id", *key]]

    # Nulos y valores de relleno por columna de texto
    text_cols = [c for c in df.columns if c not in AMOUNT_COLUMNS + DATE_COLUMNS]
    inv["placeholders"] = pd.DataFrame(
        {
            "nulos": df[text_cols].isna().sum(),
            "relleno_o_vacios": pd.Series({c: placeholder_mask(df[c]).sum() for c in text_cols}),
            "valores_distintos": df[text_cols].nunique(),
        }
    ).sort_values("relleno_o_vacios", ascending=False)

    # Destinos
    trams = split_destinations(df)
    inv["n_destinacions_raw"] = int(df["destinacio"].nunique())
    inv["n_multidesti"] = int(trams.groupby("id").size().gt(1).sum())
    inv["trams_sense_pais"] = trams.loc[trams["pais"].isna(), "tram"].value_counts().head(20)
    inv["trams_codificacio"] = trams.loc[trams["tram"].str.contains(r"\?|�", na=False), "tram"]
    inv["top_paisos"] = trams["pais"].value_counts().head(15)
    inv["city_variants"] = city_variant_groups(trams).head(20)

    # Categóricas
    inv["n_departaments"] = int(df["departament"].nunique())
    inv["n_persones"] = int(df["nom"].nunique())
    return inv


# ---------------------------------------------------------------------------
# Informe Markdown
# ---------------------------------------------------------------------------


def _table(obj: pd.DataFrame | pd.Series, empty: str = "_Ninguno._") -> str:
    if obj is None or len(obj) == 0:
        return empty
    return obj.to_markdown()


def render_report(inv: dict, info: dict) -> str:
    start, end = inv["date_range"]
    lines = [
        "# Fase 0 · Inventario de calidad de datos",
        "",
        f"_Generado el {datetime.now(UTC):%Y-%m-%d %H:%M} UTC a partir de la instantánea "
        f"descargada el {info.get('downloaded_at')}._",
        "",
        "## Resumen",
        "",
        f"- Filas: **{inv['n_rows']}**",
        f"- Última actualización de filas según el portal: {info.get('rows_updated_at')}",
        f"- Rango de fechas de inicio: {start:%Y-%m-%d} → {end:%Y-%m-%d}"
        if pd.notna(start)
        else "- Rango de fechas: no calculable",
        f"- Departamentos distintos: {inv['n_departaments']} · Personas distintas: "
        f"{inv['n_persones']}",
        f"- Columnas inesperadas en el esquema: {info.get('unexpected_columns') or 'ninguna'}",
        f"- Columnas esperadas que faltan: {info.get('missing_columns') or 'ninguna'}",
        "",
        "## Importes",
        "",
        f"- Registros sin total: {inv['total_missing']}",
        f"- Registros con total 0: {inv['total_zero']}",
        f"- Importes negativos: {inv['negative_amounts']}",
        f"- Registros donde la suma de partidas no coincide con el total: "
        f"{len(inv['total_mismatch'])}",
        "",
        _table(inv["total_mismatch"].head(20)),
        "",
        "### Valores que no se pueden leer como número",
        "",
        "```",
        json.dumps(inv["amount_parse_failures"], ensure_ascii=False, indent=2),
        "```",
        "",
        "### Estadísticos descriptivos",
        "",
        _table(inv["amounts_describe"].round(2)),
        "",
        "### Mismo importe en registros distintos (¿gasto compartido?)",
        "",
        _table(inv["shared_amounts"].head(25)),
        "",
        "## Fechas",
        "",
        "Valores que no se pueden leer como fecha:",
        "",
        "```",
        json.dumps(inv["date_parse_failures"], ensure_ascii=False, indent=2),
        "```",
        "",
        f"- Fechas de inicio en el futuro: {inv['future_dates']}",
        f"- Registros con fin anterior al inicio: {len(inv['end_before_start'])}",
        "",
        _table(inv["end_before_start"]),
        "",
        "Duración en días (inclusive):",
        "",
        _table(inv["duration_describe"].round(1)),
        "",
        "Viajes de más de 21 días (revisar):",
        "",
        _table(inv["long_trips"]),
        "",
        "## Duplicados",
        "",
        f"- Ids duplicados: {inv['duplicated_ids']}",
        f"- Misma persona, fecha y destino: {len(inv['duplicated_trips'])} registros",
        "",
        _table(inv["duplicated_trips"]),
        "",
        "## Destinos",
        "",
        f"- Valores distintos del campo destino: {inv['n_destinacions_raw']}",
        f"- Viajes con varios destinos: {inv['n_multidesti']}",
        "",
        "### Tramos sin país entre paréntesis",
        "",
        _table(inv["trams_sense_pais"]),
        "",
        "### Posibles problemas de codificación",
        "",
        _table(inv["trams_codificacio"]),
        "",
        "### Posibles variantes de la misma ciudad (heurística, revisar)",
        "",
        _table(inv["city_variants"]),
        "",
        "### Países más frecuentes (tal como vienen escritos)",
        "",
        _table(inv["top_paisos"]),
        "",
        "## Campos de texto: nulos y valores de relleno",
        "",
        _table(inv["placeholders"]),
        "",
        "## Decisiones de limpieza",
        "",
        "_Las reglas para cada problema de este informe están en "
        "[docs/decisions/0002-reglas-de-limpieza.md]"
        "(../docs/decisions/0002-reglas-de-limpieza.md). "
        "Si aparece un problema nuevo, añádelo allí antes de tocar el código._",
        "",
    ]
    return "\n".join(lines)


def run_profile(snapshot_dir: Path, reports_dir: Path) -> Path:
    df, info = load_snapshot(snapshot_dir)
    report = render_report(build_inventory(df), info)
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / "fase0_inventario.md"
    out.write_text(report, encoding="utf-8")
    return out
