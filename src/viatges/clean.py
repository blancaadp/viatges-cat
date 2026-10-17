"""Fase 1: limpieza y normalización.

Implementa las reglas de `docs/decisions/0002-reglas-de-limpieza.md`. Resumen:

- Las columnas originales se conservan; lo limpio va en columnas nuevas (`*_clean`, `ambit`…).
- Nada se borra: los problemas se señalan con columnas `flag_*`.
- Las reglas generales están aquí; las excepciones caso a caso, en `data/manual/`.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from viatges.profiling import (
    city_variant_groups,
    load_snapshot,
    parse_amount,
    parse_date,
    placeholder_mask,
    strip_accents,
)
from viatges.schema import AMOUNT_COLUMNS, COST_COLUMNS

log = logging.getLogger(__name__)

ROUNDING_TOLERANCE = 5.0  # € de diferencia entre suma de partidas y total que aceptamos
MAX_PLAUSIBLE_DAYS = 21
TEXT_COLUMNS = ["observacions", "comitiva", "altres_despeses_detall", "agenda"]
HOME_COUNTRY = "ES"

# ---------------------------------------------------------------------------
# Diccionarios manuales
# ---------------------------------------------------------------------------


@dataclass
class Manual:
    paisos: pd.DataFrame  # variant, pais, iso2
    ciutats: pd.DataFrame  # variant, ciutat, iso2
    departaments: pd.DataFrame  # departament, departament_clean, ambit
    correcciones: pd.DataFrame  # id, campo, valor_nuevo, motivo, fuente


def load_manual(manual_dir: Path) -> Manual:
    def read(name: str) -> pd.DataFrame:
        return pd.read_csv(manual_dir / name, dtype="string", keep_default_na=False)

    return Manual(
        paisos=read("paisos.csv"),
        ciutats=read("ciutats.csv"),
        departaments=read("departaments.csv"),
        correcciones=read("correcciones.csv"),
    )


def lookup_key(text: str) -> str:
    """Clave para buscar en los diccionarios: sin acentos, mayúsculas ni puntuación."""
    return re.sub(r"[^a-z0-9?]", "", strip_accents(text))


# ---------------------------------------------------------------------------
# Correcciones caso a caso
# ---------------------------------------------------------------------------


def apply_corrections(df: pd.DataFrame, corrections: pd.DataFrame) -> pd.DataFrame:
    """Sustituye valores puntuales y deja constancia en la columna `correccions`."""
    out = df.copy()
    out["correccions"] = ""
    for row in corrections.itertuples(index=False):
        mask = out["id"] == row.id
        if not mask.any():
            log.warning("Corrección para un id que no existe: %s", row.id)
            continue
        if row.campo not in out.columns:
            raise ValueError(f"Corrección sobre una columna desconocida: {row.campo}")
        out.loc[mask, row.campo] = row.valor_nuevo
        out.loc[mask, "correccions"] += f"{row.campo};"
    out["correccions"] = out["correccions"].str.rstrip(";").replace("", pd.NA)
    return out


# ---------------------------------------------------------------------------
# Importes
# ---------------------------------------------------------------------------

# Orden importante: la primera categoría que encaja gana
_ZERO_REASONS = [
    ("pendent", r"en curs|s.estan gestionant|pendent|en tr[àa]mit"),
    ("imputat_a_altre", r"imput|inclo[sue]|inclòs|desglossar|registre del viatge"),
    ("pagat_per_tercers", r"assumid|a c[àa]rrec d|pagad|sufragad|financ|convida|invita"),
]


def classify_zero_total(observacions: pd.Series) -> pd.Series:
    text = observacions.astype("string").str.lower().fillna("")
    out = pd.Series("sense_despesa", index=observacions.index, dtype="string")
    assigned = pd.Series(False, index=observacions.index)
    for label, pattern in _ZERO_REASONS:
        hit = text.str.contains(pattern, regex=True) & ~assigned
        out[hit] = label
        assigned |= hit
    return out


def clean_amounts(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in AMOUNT_COLUMNS:
        out[f"{col}_clean"] = parse_amount(df[col])[0]
    parts = out[[f"{c}_clean" for c in COST_COLUMNS]]
    all_parts = parts.notna().all(axis=1)
    parts_sum = parts.sum(axis=1)

    # Total vacío pero partidas completas -> la suma
    fill = out["total_clean"].isna() & all_parts
    out.loc[fill, "total_clean"] = parts_sum[fill]
    out["flag_total_calculat"] = fill.fillna(False).astype(bool)

    # Suma de partidas ≠ total: redondeo tolerable o inconsistencia
    diff = (out["total_clean"] - parts_sum).abs().where(all_parts)
    in_range = diff.between(0.01, ROUNDING_TOLERANCE, inclusive="right")
    out["flag_redondeig"] = in_range.fillna(False).astype(bool)
    out["flag_import_inconsistent"] = (diff > ROUNDING_TOLERANCE).fillna(False).astype(bool)

    # Total = 0: por qué
    zero = (out["total_clean"] == 0).fillna(False).astype(bool)
    out["motiu_import_zero"] = classify_zero_total(out["observacions"]).where(zero)
    pending = (out["motiu_import_zero"] == "pendent").fillna(False).astype(bool)
    out.loc[pending, [f"{c}_clean" for c in AMOUNT_COLUMNS]] = pd.NA

    out["flag_import_incomplet"] = out[[f"{c}_clean" for c in AMOUNT_COLUMNS]].isna().any(axis=1)
    return out


# ---------------------------------------------------------------------------
# Fechas
# ---------------------------------------------------------------------------


def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["data_inici_clean"] = parse_date(df["data_inici"])[0].dt.date
    out["data_fi_clean"] = parse_date(df["data_fi"])[0].dt.date
    days = (
        pd.to_datetime(out["data_fi_clean"]) - pd.to_datetime(out["data_inici_clean"])
    ).dt.days + 1
    out["durada_dies"] = days.astype("Int64")
    out["flag_durada_sospitosa"] = (out["durada_dies"] > MAX_PLAUSIBLE_DAYS).fillna(False)
    return out


# ---------------------------------------------------------------------------
# Duplicados
# ---------------------------------------------------------------------------


def _id_priority(ids: pd.Series) -> pd.DataFrame:
    """racc* antes que CMH/ACC (destino mejor informado); después, el número más bajo."""
    prefix = ids.str.extract(r"^([A-Za-z]+)")[0]
    number = pd.to_numeric(ids.str.extract(r"(\d+)")[0], errors="coerce")
    return pd.DataFrame({"rank": (~prefix.str.startswith("racc")).astype(int), "num": number})


def mark_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Misma persona y fecha de inicio: mismo total -> duplicado; distinto -> desdoblamiento."""
    out = df.copy()
    out["nom_clau"] = out["nom"].map(lambda s: " ".join(str(s).split()).casefold())
    order = pd.concat([out, _id_priority(out["id"])], axis=1).sort_values(
        ["nom_clau", "data_inici_clean", "rank", "num"]
    )
    group_key = ["nom_clau", "data_inici_clean"]
    order["grup_viatge"] = order.groupby(group_key)["id"].transform("first")

    has_total = order["total_clean"].notna()
    same_total_key = [*group_key, "total_clean"]
    dup = order.duplicated(same_total_key, keep="first") & has_total
    first_with_total = order.groupby(same_total_key, dropna=False)["id"].transform("first")
    order["flag_duplicat"] = dup
    order["duplicat_de"] = first_with_total.where(dup)

    kept = (~order["flag_duplicat"]).groupby([order[k] for k in group_key]).transform("sum")
    order["flag_possible_desdoblament"] = kept > 1

    cols = ["grup_viatge", "flag_duplicat", "duplicat_de", "flag_possible_desdoblament"]
    out[cols] = order[cols]
    return out.drop(columns="nom_clau")


# ---------------------------------------------------------------------------
# Destinos
# ---------------------------------------------------------------------------

_SEPARATORS = "/;\n"
_LEADING_JUNK = re.compile(r"^[\s,;/.\-\"'“”]*(?:i\s+)?")
_TRAILING_JUNK = re.compile(r"[\s,;/\-\"'“”]+$")
_TRAM_RE = re.compile(r"^(?P<ciutat>[^()]*?)\s*(?:\((?P<pais>[^()]*)\))?\.?$")


def split_trams(destinacio: str) -> list[str]:
    """Separa un campo de destino en tramos.

    Corta por `/`, `;` o salto de línea fuera de paréntesis, y también justo después de
    un paréntesis de país si detrás viene otro destino ("Tànger (Marroc) i Rabat (Marroc)").
    Las comas sueltas no cortan, para no romper "Washington, D.C.".
    """
    trams, buf, depth = [], "", 0
    for ch in destinacio:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        if depth == 0 and ch in _SEPARATORS:
            trams.append(buf)
            buf = ""
            continue
        buf += ch
        if depth == 0 and ch == ")":
            trams.append(buf)
            buf = ""
    trams.append(buf)
    cleaned = (_TRAILING_JUNK.sub("", _LEADING_JUNK.sub("", t)) for t in trams)
    return [t for t in cleaned if t]


def normalize_place(text: str | None) -> str | None:
    """Arreglos mecánicos de grafía: Unicode, espacios, mayúsculas, `l.l` -> `l·l`."""
    if text is None or pd.isna(text):
        return None
    t = " ".join(unicodedata.normalize("NFC", text).split()).strip(" .\"'")
    t = re.sub(r"l\.l", "l·l", t, flags=re.IGNORECASE)
    if t.isupper():
        t = " ".join(w[:1].upper() + w[1:] for w in t.lower().split())
    return t or None


def build_trams(df: pd.DataFrame, manual: Manual) -> pd.DataFrame:
    """Una fila por tramo con ciudad y país normalizados (ISO 3166-1 alfa-2)."""
    paisos = {lookup_key(r.variant): (r.pais, r.iso2) for r in manual.paisos.itertuples()}
    iso_name = {iso: name for name, iso in paisos.values()}
    ciutats = {lookup_key(r.variant): (r.ciutat, r.iso2) for r in manual.ciutats.itertuples()}
    for name, iso in set(ciutats.values()):  # la forma canónica también se reconoce
        ciutats.setdefault(lookup_key(name), (name, iso))

    rows = []
    for viatge_id, destinacio in df[["id", "destinacio"]].itertuples(index=False):
        for ordre, tram in enumerate(split_trams(str(destinacio or "")), start=1):
            m = _TRAM_RE.match(tram)
            ciutat_raw = normalize_place(m["ciutat"]) if m else normalize_place(tram)
            pais_raw = normalize_place(m["pais"]) if m else None

            iso = paisos.get(lookup_key(pais_raw), (None, None))[1] if pais_raw else None
            pais_mapejat = iso is not None
            ciutat, ciutat_mapejada = ciutat_raw, False
            if ciutat_raw:
                key = lookup_key(ciutat_raw)
                if key in ciutats and (iso is None or ciutats[key][1] == iso):
                    ciutat, city_iso = ciutats[key]
                    ciutat_mapejada = True
                    iso = iso or city_iso
                elif pais_raw is None and key in paisos:  # el tramo es un país: "Japó"
                    iso, ciutat = paisos[key][1], None
                    pais_mapejat = True
            rows.append(
                {
                    "id": viatge_id,
                    "ordre": ordre,
                    "tram": tram,
                    "ciutat_raw": ciutat_raw,
                    "pais_raw": pais_raw,
                    "ciutat": ciutat,
                    "pais": iso_name.get(iso) if iso else None,
                    "iso2": iso,
                    "ciutat_mapejada": ciutat_mapejada,
                    "pais_mapejat": pais_mapejat,
                }
            )
    return pd.DataFrame(rows)


def summarize_trams(df: pd.DataFrame, trams: pd.DataFrame) -> pd.DataFrame:
    """Añade a cada viaje sus países y si es realmente un viaje al extranjero."""
    per_trip = trams.groupby("id").agg(
        n_trams=("ordre", "size"),
        paisos_iso2=("iso2", lambda s: ";".join(dict.fromkeys(s.dropna()))),
        flag_desti_sense_pais=("iso2", lambda s: s.isna().any()),
        flag_no_estranger=("iso2", lambda s: s.notna().all() and (s == HOME_COUNTRY).all()),
    )
    out = df.merge(per_trip, left_on="id", right_index=True, how="left")
    out["n_trams"] = out["n_trams"].fillna(0).astype(int)
    for flag in ["flag_desti_sense_pais", "flag_no_estranger"]:
        out[flag] = out[flag].fillna(flag == "flag_desti_sense_pais").astype(bool)
    return out


# ---------------------------------------------------------------------------
# Departamentos y textos
# ---------------------------------------------------------------------------


def clean_departments(df: pd.DataFrame, departaments: pd.DataFrame) -> pd.DataFrame:
    key = df["departament"].map(lambda s: " ".join(str(s).split()))
    mapping = departaments.set_index("departament")
    out = df.copy()
    out["departament_clean"] = key.map(mapping["departament_clean"]).fillna(key)
    out["ambit"] = key.map(mapping["ambit"])
    return out


def clean_texts(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in TEXT_COLUMNS:
        if col not in out:
            out[col] = pd.NA
        text = out[col].astype("string").str.strip()
        out[f"{col}_clean"] = text.mask(placeholder_mask(out[col]))
    return out


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------


def clean(df: pd.DataFrame, manual: Manual) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (viajes, tramos) limpios."""
    viatges = apply_corrections(df, manual.correcciones)
    viatges = clean_amounts(viatges)
    viatges = clean_dates(viatges)
    viatges = mark_duplicates(viatges)
    trams = build_trams(viatges, manual)
    viatges = summarize_trams(viatges, trams)
    viatges = clean_departments(viatges, manual.departaments)
    viatges = clean_texts(viatges)
    return viatges, trams


def _table(obj: pd.DataFrame | pd.Series, empty: str = "_Ninguno._") -> str:
    return obj.to_markdown() if len(obj) else empty


def render_report(viatges: pd.DataFrame, trams: pd.DataFrame, info: dict) -> str:
    flags = viatges[[c for c in viatges.columns if c.startswith("flag_")]].sum()
    unmapped_countries = trams.loc[~trams["pais_mapejat"] & trams["pais_raw"].notna(), "pais_raw"]
    no_country = trams.loc[trams["iso2"].isna(), "tram"]
    remaining_variants = city_variant_groups(trams.dropna(subset=["ciutat"]))
    dups = viatges.loc[viatges["flag_duplicat"], ["id", "duplicat_de", "nom", "total_clean"]]
    splits = viatges.loc[
        viatges["flag_possible_desdoblament"],
        ["grup_viatge", "id", "nom", "data_inici_clean", "total_clean"],
    ].sort_values(["grup_viatge", "id"])
    lines = [
        "# Fase 1 · Resultado de la limpieza",
        "",
        f"_Instantánea descargada el {info.get('downloaded_at', '?')}. "
        "Reglas: [ADR 0002](../docs/decisions/0002-reglas-de-limpieza.md)._",
        "",
        f"- Viajes: **{len(viatges)}** · tramos de destino: **{len(trams)}**",
        f"- Correcciones manuales aplicadas: {int(viatges['correccions'].notna().sum())}",
        f"- Ciudades distintas tras normalizar: {trams['ciutat'].nunique()} "
        f"(antes {trams['ciutat_raw'].nunique()})",
        f"- Países distintos: {trams['iso2'].nunique()}",
        f"- Departamentos sin ámbito asignado: {int(viatges['ambit'].isna().sum())}",
        "",
        "## Señales (`flag_*`)",
        "",
        _table(flags.rename("registros")),
        "",
        "## Motivo de los importes a cero",
        "",
        _table(viatges["motiu_import_zero"].value_counts()),
        "",
        "## Duplicados descartados",
        "",
        _table(dups.set_index("id")),
        "",
        "## Posibles desdoblamientos (revisar)",
        "",
        _table(splits.set_index("grup_viatge")),
        "",
        "## Pendiente de completar en `data/manual/`",
        "",
        "### Países sin mapear (`paisos.csv`)",
        "",
        _table(unmapped_countries.value_counts()),
        "",
        "### Tramos sin país",
        "",
        _table(no_country.value_counts()),
        "",
        "### Ciudades que aún parecen variantes (`ciutats.csv`, heurística)",
        "",
        _table(remaining_variants),
        "",
        "### Departamentos sin ámbito (`departaments.csv`)",
        "",
        _table(viatges.loc[viatges["ambit"].isna(), "departament"].value_counts()),
        "",
    ]
    return "\n".join(lines)


def run_clean(snapshot_dir: Path, manual_dir: Path, processed_dir: Path, reports_dir: Path) -> Path:
    df, info = load_snapshot(snapshot_dir)
    viatges, trams = clean(df, load_manual(manual_dir))
    out_dir = processed_dir / snapshot_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    viatges.to_csv(out_dir / "viatges.csv", index=False)
    trams.to_csv(out_dir / "trams.csv", index=False)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "fase1_neteja.md").write_text(
        render_report(viatges, trams, info), encoding="utf-8"
    )
    return out_dir
