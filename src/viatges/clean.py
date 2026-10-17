"""Fase 1: neteja i normalització.

Implementa les regles de `docs/decisions/0002-regles-de-neteja.md`. Resum:

- Les columnes originals es conserven; el que és net va en columnes noves (`*_clean`, `ambit`…).
- No s'esborra res: els problemes s'assenyalen amb columnes `flag_*`.
- Les regles generals són aquí; les excepcions cas per cas, a `data/manual/`.
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

ROUNDING_TOLERANCE = 5.0  # € de diferència acceptada entre la suma de partides i el total
MAX_PLAUSIBLE_DAYS = 21
TEXT_COLUMNS = ["observacions", "comitiva", "altres_despeses_detall", "agenda"]
HOME_COUNTRY = "ES"

# Camps de revisió manual: no existeixen al dataset, els crea `correccions.csv`
REVIEW_FIELDS = ["revisio_duplicat_de", "revisio_desdoblament"]
SPLIT_DECISIONS = {"complementari", "independent", "pendent"}

# ---------------------------------------------------------------------------
# Diccionaris manuals
# ---------------------------------------------------------------------------


@dataclass
class Manual:
    paisos: pd.DataFrame  # variant, pais, iso2
    ciutats: pd.DataFrame  # variant, ciutat, iso2
    departaments: pd.DataFrame  # departament, departament_clean, ambit
    correccions: pd.DataFrame  # id, camp, valor_nou, motiu, font


def load_manual(manual_dir: Path) -> Manual:
    def read(name: str) -> pd.DataFrame:
        return pd.read_csv(manual_dir / name, dtype="string", keep_default_na=False)

    return Manual(
        paisos=read("paisos.csv"),
        ciutats=read("ciutats.csv"),
        departaments=read("departaments.csv"),
        correccions=read("correccions.csv"),
    )


def lookup_key(text: str) -> str:
    """Clau per buscar als diccionaris: sense accents, majúscules ni puntuació."""
    return re.sub(r"[^a-z0-9?]", "", strip_accents(text))


# ---------------------------------------------------------------------------
# Correccions cas per cas
# ---------------------------------------------------------------------------


def apply_corrections(df: pd.DataFrame, corrections: pd.DataFrame) -> pd.DataFrame:
    """Substitueix valors puntuals i en deixa constància a la columna `correccions`."""
    out = df.copy()
    out["correccions"] = ""
    for field in REVIEW_FIELDS:
        out[field] = pd.Series(pd.NA, index=out.index, dtype="string")
    for row in corrections.itertuples(index=False):
        mask = out["id"] == row.id
        if not mask.any():
            log.warning("Correcció per a un id que no existeix: %s", row.id)
            continue
        if row.camp not in out.columns:
            raise ValueError(f"Correcció sobre una columna desconeguda: {row.camp}")
        out.loc[mask, row.camp] = row.valor_nou
        out.loc[mask, "correccions"] += f"{row.camp};"
    out["correccions"] = out["correccions"].str.rstrip(";").replace("", pd.NA)
    return out


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

# L'ordre importa: guanya la primera categoria que encaixa
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

    # Total buit però partides completes -> la suma
    fill = out["total_clean"].isna() & all_parts
    out.loc[fill, "total_clean"] = parts_sum[fill]
    out["flag_total_calculat"] = fill.fillna(False).astype(bool)

    # Suma de partides ≠ total: arrodoniment tolerable o inconsistència
    diff = (out["total_clean"] - parts_sum).abs().where(all_parts)
    in_range = diff.between(0.01, ROUNDING_TOLERANCE, inclusive="right")
    out["flag_redondeig"] = in_range.fillna(False).astype(bool)
    out["flag_import_inconsistent"] = (diff > ROUNDING_TOLERANCE).fillna(False).astype(bool)

    # Total = 0: per què
    zero = (out["total_clean"] == 0).fillna(False).astype(bool)
    out["motiu_import_zero"] = classify_zero_total(out["observacions"]).where(zero)
    pending = (out["motiu_import_zero"] == "pendent").fillna(False).astype(bool)
    out.loc[pending, [f"{c}_clean" for c in AMOUNT_COLUMNS]] = pd.NA

    out["flag_import_incomplet"] = out[[f"{c}_clean" for c in AMOUNT_COLUMNS]].isna().any(axis=1)
    return out


# ---------------------------------------------------------------------------
# Dates
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
# Duplicats
# ---------------------------------------------------------------------------


def _id_priority(ids: pd.Series) -> pd.DataFrame:
    """racc* abans que CMH/ACC (destinació més ben informada); després, el número més baix."""
    prefix = ids.str.extract(r"^([A-Za-z]+)")[0]
    number = pd.to_numeric(ids.str.extract(r"(\d+)")[0], errors="coerce")
    return pd.DataFrame({"rank": (~prefix.str.startswith("racc")).astype(int), "num": number})


def mark_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Mateixa persona i data d'inici: mateix total -> duplicat; diferent -> desdoblament.

    Les decisions revisades a mà (`revisio_*`, des de `correccions.csv`) passen per davant
    de la detecció automàtica:

    - `revisio_duplicat_de = <id>`: el registre és un duplicat de `<id>`.
    - `revisio_desdoblament = complementari`: mateix viatge amb els costos repartits; se
      sumen i es compta una vegada.
    - `revisio_desdoblament = independent`: viatges diferents; cadascun és el seu grup.
    - `revisio_desdoblament = pendent`: revisat però sense resoldre; continua marcat.
    """
    out = df.copy()
    for field in REVIEW_FIELDS:
        if field not in out:
            out[field] = pd.Series(pd.NA, index=out.index, dtype="string")
    unknown = set(out["revisio_desdoblament"].dropna()) - SPLIT_DECISIONS
    if unknown:
        raise ValueError(f"Decisió de desdoblament desconeguda: {sorted(unknown)}")

    out["nom_clau"] = out["nom"].map(lambda s: " ".join(str(s).split()).casefold())
    order = pd.concat([out, _id_priority(out["id"])], axis=1).sort_values(
        ["nom_clau", "data_inici_clean", "rank", "num"]
    )
    # Un viatge independent forma el seu propi grup
    independent = (order["revisio_desdoblament"] == "independent").fillna(False)
    order["clau_grup"] = order["data_inici_clean"].astype(str)
    order.loc[independent, "clau_grup"] = order["clau_grup"] + "|" + order["id"]
    group_key = ["nom_clau", "clau_grup"]

    has_total = order["total_clean"].notna()
    same_total_key = [*group_key, "total_clean"]
    dup = order.duplicated(same_total_key, keep="first") & has_total
    first_with_total = order.groupby(same_total_key, dropna=False)["id"].transform("first")
    manual_dup = order["revisio_duplicat_de"].notna()
    order["flag_duplicat"] = dup | manual_dup
    order["duplicat_de"] = order["revisio_duplicat_de"].fillna(first_with_total.where(dup))

    groups = [order[k] for k in group_key]
    first_kept = order["id"].where(~order["flag_duplicat"]).groupby(groups).transform("first")
    order["grup_viatge"] = first_kept.fillna(order.groupby(groups)["id"].transform("first"))

    kept = (~order["flag_duplicat"]).groupby(groups).transform("sum")
    resolved = order["revisio_desdoblament"].isin({"complementari", "independent"}).fillna(False)
    resolved_group = resolved.groupby(groups).transform("any")
    order["flag_possible_desdoblament"] = (kept > 1) & ~resolved_group

    cols = ["grup_viatge", "flag_duplicat", "duplicat_de", "flag_possible_desdoblament"]
    out[cols] = order[cols]
    return out.drop(columns="nom_clau")


# ---------------------------------------------------------------------------
# Destinacions
# ---------------------------------------------------------------------------

_SEPARATORS = "/;\n"
_LEADING_JUNK = re.compile(r"^[\s,;/.\-\"'“”]*(?:i\s+)?")
_TRAILING_JUNK = re.compile(r"[\s,;/\-\"'“”]+$")
_TRAM_RE = re.compile(r"^(?P<ciutat>[^()]*?)\s*(?:\((?P<pais>[^()]*)\))?\.?$")


def split_trams(destinacio: str) -> list[str]:
    """Separa un camp de destinació en trams.

    Talla per `/`, `;` o salt de línia fora de parèntesis, i també just després d'un
    parèntesi de país si darrere ve una altra destinació ("Tànger (Marroc) i Rabat (Marroc)").
    Les comes soles no tallen, per no trencar "Washington, D.C.".
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
    """Arranjaments mecànics de grafia: Unicode, espais, majúscules, `l.l` -> `l·l`."""
    if text is None or pd.isna(text):
        return None
    t = " ".join(unicodedata.normalize("NFC", text).split()).strip(" .\"'")
    t = re.sub(r"l\.l", "l·l", t, flags=re.IGNORECASE)
    if t.isupper():
        t = " ".join(w[:1].upper() + w[1:] for w in t.lower().split())
    return t or None


def build_trams(df: pd.DataFrame, manual: Manual) -> pd.DataFrame:
    """Una fila per tram amb ciutat i país normalitzats (ISO 3166-1 alfa-2)."""
    paisos = {lookup_key(r.variant): (r.pais, r.iso2) for r in manual.paisos.itertuples()}
    iso_name = {iso: name for name, iso in paisos.values()}
    ciutats = {lookup_key(r.variant): (r.ciutat, r.iso2) for r in manual.ciutats.itertuples()}
    for name, iso in set(ciutats.values()):  # la forma canònica també es reconeix
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
                elif pais_raw is None and key in paisos:  # el tram és un país: "Japó"
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
    """Afegeix a cada viatge els seus països i si és realment un viatge a l'estranger."""
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
# Departaments i textos
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
# Orquestració
# ---------------------------------------------------------------------------


def clean(df: pd.DataFrame, manual: Manual) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (viatges, trams) nets."""
    viatges = apply_corrections(df, manual.correccions)
    viatges = clean_amounts(viatges)
    viatges = clean_dates(viatges)
    viatges = mark_duplicates(viatges)
    trams = build_trams(viatges, manual)
    viatges = summarize_trams(viatges, trams)
    viatges = clean_departments(viatges, manual.departaments)
    viatges = clean_texts(viatges)
    return viatges, trams


def _table(obj: pd.DataFrame | pd.Series, empty: str = "_Cap._") -> str:
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
        "# Fase 1 · Resultat de la neteja",
        "",
        f"_Instantània descarregada el {info.get('downloaded_at', '?')}. "
        "Regles: [ADR 0002](../docs/decisions/0002-regles-de-neteja.md)._",
        "",
        f"- Viatges: **{len(viatges)}** · trams de destinació: **{len(trams)}**",
        f"- Correccions manuals aplicades: {int(viatges['correccions'].notna().sum())}",
        f"- Ciutats diferents després de normalitzar: {trams['ciutat'].nunique()} "
        f"(abans {trams['ciutat_raw'].nunique()})",
        f"- Països diferents: {trams['iso2'].nunique()}",
        f"- Departaments sense àmbit assignat: {int(viatges['ambit'].isna().sum())}",
        "",
        "## Senyals (`flag_*`)",
        "",
        _table(flags.rename("registres")),
        "",
        "## Motiu dels imports a zero",
        "",
        _table(viatges["motiu_import_zero"].value_counts()),
        "",
        "## Duplicats descartats",
        "",
        _table(dups.set_index("id")),
        "",
        "## Possibles desdoblaments (revisar)",
        "",
        _table(splits.set_index("grup_viatge")),
        "",
        "## Pendent de completar a `data/manual/`",
        "",
        "### Països sense mapejar (`paisos.csv`)",
        "",
        _table(unmapped_countries.value_counts()),
        "",
        "### Trams sense país",
        "",
        _table(no_country.value_counts()),
        "",
        "### Ciutats que encara semblen variants (`ciutats.csv`, heurística)",
        "",
        _table(remaining_variants),
        "",
        "### Departaments sense àmbit (`departaments.csv`)",
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
