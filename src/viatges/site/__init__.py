"""Fase 4: genera el web estàtic a partir de `data/viatges.sqlite` (ADR 0006).

El resultat és una carpeta (`site/`) amb HTML, CSS, JS i les dades en JSON i CSV, que es
pot publicar tal qual a Vercel. Els gràfics es dibuixen aquí en SVG, de manera que
es veuen encara que el navegador no executi JavaScript.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import shutil
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from viatges.schema import COLUMNS

log = logging.getLogger(__name__)

HERE = Path(__file__).parent
DATASET_URL = "https://analisi.transparenciacatalunya.cat/d/5kte-hque"
REPO_URL = "https://github.com/blancaadp/viatges-cat"
MONTHS = ["gener", "febrer", "març", "abril", "maig", "juny", "juliol", "agost",
          "setembre", "octubre", "novembre", "desembre"]  # fmt: skip

# ---------------------------------------------------------------------------
# Format català
# ---------------------------------------------------------------------------


def fmt_int(value: float) -> str:
    return f"{round(value):,}".replace(",", ".")


def fmt_eur(value: float | None, decimals: int = 0) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    text = f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} €"


def fmt_compact_eur(value: float) -> str:
    """1.234.567 -> '1,2 M€'; 45.000 -> '45 k€'."""
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}".replace(".", ",") + " M€"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f} k€"
    return f"{value:.0f} €"


def fmt_pct(value: float) -> str:
    return f"{value:.1f}".replace(".", ",") + " %"


def fmt_date(value: str | None, long: bool = False) -> str:
    if value is None or pd.isna(value) or not str(value).strip():
        return "—"
    d = date.fromisoformat(str(value)[:10])
    if long:
        prep = "d'" if MONTHS[d.month - 1][0] in "aeiou" else "de "
        return f"{d.day} {prep}{MONTHS[d.month - 1]} de {d.year}"
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _key(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text))
    return " ".join(
        "".join(c for c in decomposed if not unicodedata.combining(c)).split()
    ).casefold()


# ---------------------------------------------------------------------------
# Gràfics en SVG
# ---------------------------------------------------------------------------


def _nice_step(maximum: float, ticks: int = 4) -> float:
    raw = maximum / ticks
    magnitude = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    for factor in (1, 2, 2.5, 5, 10):
        if raw <= factor * magnitude:
            return factor * magnitude
    return 10 * magnitude


def column_chart(items: list[dict], title: str) -> str:
    """Columnes verticals d'una sola sèrie. `items`: label, value, tip, highlight (opcional)."""
    width, height = 640, 260
    left, right, top, bottom = 56, 8, 24, 28
    plot_w, plot_h = width - left - right, height - top - bottom
    maximum = max((i["value"] for i in items), default=0) or 1
    step = _nice_step(maximum)
    y_max = step * math.ceil(maximum / step)
    band = plot_w / max(len(items), 1)
    bar_w = min(24, band * 0.6)

    def y(v: float) -> float:
        return top + plot_h - v / y_max * plot_h

    parts = [
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{title}" preserveAspectRatio="xMidYMid meet">'
    ]
    tick = 0.0
    while tick <= y_max + 1e-9:
        ty = y(tick)
        cls = "baseline" if tick == 0 else "grid"
        parts.append(
            f'<line class="{cls}" x1="{left}" x2="{width - right}" y1="{ty:.1f}" y2="{ty:.1f}"/>'
        )
        parts.append(
            f'<text class="tick" x="{left - 8}" y="{ty + 4:.1f}" text-anchor="end">'
            f"{fmt_compact_eur(tick) if tick else '0'}</text>"
        )
        tick += step
    top_item = max(items, key=lambda i: i["value"]) if items else None
    for idx, item in enumerate(items):
        cx = left + band * idx + band / 2
        x0, x1 = cx - bar_w / 2, cx + bar_w / 2
        y0, base = y(item["value"]), y(0)
        r = min(4, (base - y0) / 2, bar_w / 2)
        path = (
            f"M{x0:.1f},{base:.1f} V{y0 + r:.1f} Q{x0:.1f},{y0:.1f} {x0 + r:.1f},{y0:.1f} "
            f"H{x1 - r:.1f} Q{x1:.1f},{y0:.1f} {x1:.1f},{y0 + r:.1f} V{base:.1f} Z"
        )
        parts.append(f'<path class="bar" d="{path}"/>')
        parts.append(
            f'<text class="tick x" x="{cx:.1f}" y="{height - 8}" text-anchor="middle">'
            f"{item['label']}</text>"
        )
        if item is top_item:
            parts.append(
                f'<text class="value" x="{cx:.1f}" y="{y0 - 6:.1f}" text-anchor="middle">'
                f"{fmt_compact_eur(item['value'])}</text>"
            )
        # Zona de hover: tota la franja, més gran que la columna
        parts.append(
            f'<rect class="hit" x="{left + band * idx:.1f}" y="{top}" width="{band:.1f}" '
            f'height="{plot_h}" tabindex="0" data-tip="{item["tip"]}" '
            f'aria-label="{item["tip"]}"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


@dataclass
class BarRow:
    label: str
    value: float
    display: str
    tip: str
    href: str | None = None


def bar_rows(rows: list[BarRow]) -> list[dict]:
    """Barres horitzontals en HTML: amplada relativa al màxim."""
    maximum = max((r.value for r in rows), default=0) or 1
    return [{**r.__dict__, "pct": r.value / maximum * 100} for r in rows]


# Partides de despesa, en l'ordre en què es mostren (la columna de la base de dades i l'etiqueta)
CATEGORIES = [
    ("dietes_eur", "Dietes i manutenció"),
    ("allotjament_eur", "Allotjament"),
    ("transport_eur", "Transport"),
    ("altres_despeses_eur", "Altres despeses"),
]


def category_shares(frame: pd.DataFrame) -> dict | None:
    """Distribució percentual de la despesa per partida.

    El percentatge es calcula sobre la suma de les quatre partides, no sobre `total_eur`,
    perquè així les quatre parts sumen sempre el 100 %. Retorna None si no hi ha cap import.
    """
    sums = frame[[col for col, _ in CATEGORIES]].fillna(0).sum()
    total = float(sums.sum())
    if total <= 0:
        return None
    parts = []
    for (_col, label), value in zip(CATEGORIES, sums, strict=True):
        pct = float(value) / total * 100
        parts.append(
            {
                "label": label,
                "value": float(value),
                "eur": fmt_eur(value),
                "pct": pct,
                "pct_text": fmt_pct(pct),
                "tip": f"{label}: {fmt_eur(value)} ({fmt_pct(pct)})",
            }
        )
    top = max(parts, key=lambda p: p["value"])
    return {"total": total, "parts": parts, "top": top}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _key(text)).strip("-")


# ---------------------------------------------------------------------------
# Dades
# ---------------------------------------------------------------------------


@dataclass
class SiteData:
    viatges: pd.DataFrame
    trams: pd.DataFrame
    instantanies: pd.DataFrame
    correccions: pd.DataFrame


def load(db_path: Path, manual_dir: Path) -> SiteData:
    with sqlite3.connect(db_path) as con:
        viatges = pd.read_sql("SELECT * FROM viatges", con)
        trams = pd.read_sql("SELECT * FROM trams", con)
        instantanies = pd.read_sql("SELECT * FROM instantanies", con)
    for col in COLUMNS.values():  # un camp que el portal no publica no ha de trencar el web
        if col not in viatges:
            viatges[col] = None
    for col in [c for c in viatges.columns if c.startswith("flag_")] + ["exclos_analisi"]:
        viatges[col] = viatges[col].fillna(0).astype(bool)
    correccions = pd.read_csv(manual_dir / "correccions.csv", dtype="string")
    return SiteData(viatges, trams, instantanies, correccions)


def analysis_set(viatges: pd.DataFrame) -> pd.DataFrame:
    """Viatges que compten a les xifres: sense els exclosos (p99) ni els duplicats."""
    return viatges[~viatges["exclos_analisi"] & ~viatges["flag_duplicat"]]


def country_names(trams: pd.DataFrame) -> dict[str, str]:
    named = trams.dropna(subset=["iso2", "pais"]).drop_duplicates("iso2")
    return dict(zip(named["iso2"], named["pais"], strict=True))


# ---------------------------------------------------------------------------
# Pàgines
# ---------------------------------------------------------------------------


def home_context(data: SiteData, base: str) -> dict:
    v = analysis_set(data.viatges)
    trams = data.trams[data.trams["id"].isin(v["id"])]
    abroad = trams[trams["iso2"].notna() & (trams["iso2"] != "ES")]
    years = v.assign(any=v["data_inici_iso"].str[:4]).groupby("any")
    per_year = years["total_eur"].sum()
    count_year = years.size()
    current_year = str(date.today().year)
    year_items = [
        {
            "label": f"{y}*" if y == current_year else y,
            "value": float(total),
            "tip": f"{y}: {fmt_eur(total)} · {fmt_int(count_year[y])} viatges",
        }
        for y, total in per_year.items()
    ]
    ambits = (
        v.groupby("ambit")["total_eur"].agg(["sum", "size"]).sort_values("sum", ascending=False)
    )
    ambit_rows = [
        BarRow(a, float(r["sum"]), fmt_compact_eur(r["sum"]),
               f"{a}: {fmt_eur(r['sum'])} en {fmt_int(r['size'])} viatges",
               f"{base}departament/{slug(a)}/")
        for a, r in ambits.head(10).iterrows()
    ]  # fmt: skip
    names = country_names(data.trams)
    countries = abroad.drop_duplicates(["id", "iso2"]).groupby("iso2").size()
    country_rows = []
    for iso, n in countries.sort_values(ascending=False).head(10).items():
        name = names.get(iso, iso)
        tip = f"{name}: {fmt_int(n)} viatges"
        country_rows.append(BarRow(name, float(n), fmt_int(n), tip, f"{base}viatges/?pais={iso}"))
    persones = v["persona_id"].nunique()
    return {
        "kpis": [
            ("Despesa total", fmt_compact_eur(v["total_eur"].sum())),
            ("Viatges", fmt_int(len(v))),
            ("Alts càrrecs", fmt_int(persones)),
            ("Països visitats", fmt_int(abroad["iso2"].nunique())),
        ],
        "first_year": per_year.index.min(),
        "year_chart": column_chart(year_items, "Despesa per any"),
        "year_table": [(y, fmt_eur(per_year[y]), fmt_int(count_year[y])) for y in per_year.index],
        "current_year": current_year,
        "ambit_rows": bar_rows(ambit_rows),
        "country_rows": bar_rows(country_rows),
        "n_exclosos": int(data.viatges["exclos_analisi"].sum()),
        "n_duplicats": int(data.viatges["flag_duplicat"].sum()),
    }


def explorer_payload(data: SiteData) -> dict:
    """Dades compactes per a l'explorador (llista de columnes + files)."""
    v = data.viatges.sort_values("data_inici_iso", ascending=False)
    columns = ["id", "data_inici_iso", "data_fi_iso", "durada_dies", "nom", "persona",
               "persona_id", "carrec", "ambit",
               "destinacio", "paisos_iso2", "motiu", "total_eur", "exclos_analisi",
               "flag_duplicat", "motiu_import_zero"]  # fmt: skip
    rows = []
    for rec in v[columns].itertuples(index=False):
        row = []
        for value in rec:
            if isinstance(value, float) and math.isnan(value):
                value = None
            elif hasattr(value, "item"):
                value = value.item()
            row.append(value)
        rows.append(row)
    return {"columns": columns, "rows": rows, "paisos": country_names(data.trams)}


MIN_TRIPS_DAILY = 3  # mínim de viatges per entrar al rànquing de despesa diària


def people_table(data: SiteData) -> pd.DataFrame:
    """Una fila per persona, amb els viatges que compten a les xifres (sense duplicats ni p99).

    La despesa diària és la despesa total dividida pels dies totals de viatge, comptant
    només els viatges amb import i durada coneguts.
    """
    v = analysis_set(data.viatges)
    known = v[v["total_eur"].notna() & v["durada_dies"].notna()]
    latest = v.sort_values("data_inici_iso").groupby("persona_id").last()
    table = pd.DataFrame(
        {
            "persona": latest["persona"],
            "carrec": latest["carrec"],
            "ambit": latest["ambit"],
            "viatges": v.groupby("persona_id").size(),
            "total": v.groupby("persona_id")["total_eur"].sum(),
            "dies": v.groupby("persona_id")["durada_dies"].sum(),
            "total_conegut": known.groupby("persona_id")["total_eur"].sum(),
            "dies_coneguts": known.groupby("persona_id")["durada_dies"].sum(),
            "primer": v.groupby("persona_id")["data_inici_iso"].min(),
            "darrer": v.groupby("persona_id")["data_inici_iso"].max(),
        }
    )
    table["diaria"] = table["total_conegut"] / table["dies_coneguts"]
    return table.sort_values("total", ascending=False)


def people_context(data: SiteData, base: str) -> dict:
    table = people_table(data)

    def rows(column: str, frame: pd.DataFrame, n: int = 15) -> list[dict]:
        top = frame.sort_values(column, ascending=False).head(n)
        return bar_rows(
            [
                BarRow(
                    r.persona,
                    float(getattr(r, column)),
                    fmt_eur(getattr(r, column)),
                    f"{r.persona}: {fmt_eur(r.total)} en {fmt_int(r.viatges)} viatges i "
                    f"{fmt_int(r.dies)} dies ({fmt_eur(r.diaria)} / dia)",
                    f"{base}persona/{pid}/",
                )
                for pid, r in zip(top.index, top.itertuples(), strict=True)
            ]
        )

    daily = table[(table["viatges"] >= MIN_TRIPS_DAILY) & table["diaria"].notna()]
    counted = analysis_set(data.viatges)
    return {
        "category_rows": category_rows(counted, table.head(15).index, table, base),
        "total_rows": rows("total", table),
        "daily_rows": rows("diaria", daily),
        "min_trips": MIN_TRIPS_DAILY,
        "n_persones": data.viatges["persona_id"].nunique(),
        "people": people_directory(data, table),
    }


def category_rows(counted: pd.DataFrame, person_ids, table: pd.DataFrame, base: str) -> list[dict]:
    """Una fila per persona amb la distribució de la despesa per partida."""
    rows = []
    for pid in person_ids:
        trips = counted[counted["persona_id"] == pid]
        shares = category_shares(trips)
        if shares is None:
            continue
        rows.append(
            {
                "label": table.loc[pid, "persona"],
                "href": f"{base}persona/{pid}/",
                "n": fmt_int(len(trips)),
                "total": fmt_eur(shares["total"]),
                "shares": shares,
            }
        )
    return rows


def people_directory(data: SiteData, table: pd.DataFrame) -> list[dict]:
    """Totes les persones per al cercador, també les que no tenen cap viatge que compti.

    `cerca` conté totes les variants del nom i tots els càrrecs, en minúscules i sense
    accents, perquè es pugui trobar una persona per qualsevol d'ells.
    """
    v = data.viatges.sort_values("data_inici_iso")
    groups = v.groupby("persona_id")
    latest = groups.last()
    search = groups.apply(
        lambda g: _key(" ".join(map(str, [*g["nom"].unique(), *g["carrec"].unique()]))),
        include_groups=False,
    )
    people = []
    for pid, last in latest.iterrows():
        r = table.loc[pid] if pid in table.index else None
        known = r is not None and not math.isnan(r["diaria"])
        people.append(
            {
                "id": pid,
                "persona": last["persona"],
                "carrec": last["carrec"],
                "cerca": search[pid],
                "viatges": fmt_int(r["viatges"]) if r is not None else "0",
                "total": fmt_eur(r["total"]) if r is not None else "—",
                "diaria": fmt_eur(r["diaria"]) if known else "—",
                "darrer": fmt_date(last["data_inici_iso"]),
                # valors per ordenar al navegador
                "s_viatges": int(r["viatges"]) if r is not None else 0,
                "s_total": float(r["total"]) if r is not None else 0.0,
                "s_diaria": float(r["diaria"]) if known else 0.0,
                "s_darrer": str(last["data_inici_iso"] or ""),
            }
        )
    return sorted(people, key=lambda p: p["s_total"], reverse=True)


def person_context(pid: str, data: SiteData, table: pd.DataFrame, base: str) -> dict:
    trips = data.viatges[data.viatges["persona_id"] == pid].sort_values(
        "data_inici_iso", ascending=False
    )
    counted = analysis_set(trips)
    summary = table.loc[pid] if pid in table.index else None
    roles = (
        trips.assign(carrec_net=trips["carrec"].map(lambda c: " ".join(str(c).split())))
        .groupby(_key_series(trips["carrec"]))
        .agg(carrec=("carrec_net", "first"), des_de=("data_inici_iso", "min"),
             fins=("data_inici_iso", "max"), n=("id", "size"))
        .sort_values("des_de", ascending=False)
    )  # fmt: skip
    names = country_names(data.trams)
    trams = data.trams[data.trams["id"].isin(counted["id"])]
    countries = trams[trams["iso2"].notna()].drop_duplicates(["id", "iso2"]).groupby("iso2").size()
    last = trips.iloc[0]
    by_year = counted.assign(any=counted["data_inici_iso"].str[:4]).groupby("any")
    year_totals = by_year["total_eur"].sum()
    year_counts = by_year.size()
    year_chart = (
        column_chart(
            [
                {
                    "label": y,
                    "value": float(t),
                    "tip": f"{y}: {fmt_eur(t)} · {fmt_int(year_counts[y])} viatges",
                }
                for y, t in year_totals.items()
            ],
            f"Despesa per any de {trips['persona'].iloc[0]}",
        )
        if len(year_totals) >= 2
        else None
    )
    return {
        "persona": trips["persona"].iloc[0],
        "pid": pid,
        "last": {
            "id": last["id"],
            "data": fmt_date(last["data_inici_iso"], long=True),
            "destinacio": last["destinacio"],
            "carrec": last["carrec"],
        },
        "year_chart": year_chart,
        "shares": category_shares(counted),
        "variants": sorted(set(trips["nom"].map(lambda n: " ".join(str(n).split())))),
        "roles": [
            (r.carrec, fmt_date(r.des_de), fmt_date(r.fins), r.n) for r in roles.itertuples()
        ],
        "kpis": [
            ("Despesa total", fmt_eur(summary["total"]) if summary is not None else "—"),
            ("Viatges", fmt_int(len(counted))),
            ("Dies de viatge", fmt_int(counted["durada_dies"].sum())),
            ("Despesa diària", fmt_eur(summary["diaria"]) if summary is not None else "—"),
        ],
        "countries": [
            (names.get(iso, iso), n) for iso, n in countries.sort_values(ascending=False).items()
        ],
        "trips": [
            {
                "id": t.id,
                "data": fmt_date(t.data_inici_iso),
                "destinacio": t.destinacio,
                "dies": "—" if pd.isna(t.durada_dies) else fmt_int(t.durada_dies),
                "total": fmt_eur(t.total_eur),
                "marques": [
                    text
                    for flag, text in (
                        ("exclos_analisi", "Durada anòmala"),
                        ("flag_duplicat", "Duplicat"),
                    )
                    if bool(getattr(t, flag))
                ]
                + (
                    [ZERO_BADGES[t.motiu_import_zero]]
                    if isinstance(t.motiu_import_zero, str)
                    else []
                ),
            }
            for t in trips.itertuples()
        ],
        "n_no_compten": len(trips) - len(counted),
    }


def departments_context(data: SiteData, base: str) -> dict:
    v = analysis_set(data.viatges)
    rows = []
    for ambit, trips in v.groupby("ambit"):
        shares = category_shares(trips)
        if shares is None:
            continue
        rows.append(
            {
                "label": ambit,
                "href": f"{base}departament/{slug(ambit)}/",
                "n": fmt_int(len(trips)),
                "total": fmt_eur(shares["total"]),
                "shares": shares,
                "sort": shares["total"],
            }
        )
    rows.sort(key=lambda r: r["sort"], reverse=True)
    overall = category_shares(v)
    return {"rows": rows, "overall": overall}


def department_context(ambit: str, data: SiteData, base: str) -> dict:
    trips = data.viatges[data.viatges["ambit"] == ambit]
    counted = analysis_set(trips)
    names = sorted(trips["departament"].dropna().unique())
    by_year = counted.assign(any=counted["data_inici_iso"].str[:4]).groupby("any")
    year_totals = by_year["total_eur"].sum()
    year_counts = by_year.size()
    year_chart = (
        column_chart(
            [
                {
                    "label": y,
                    "value": float(t),
                    "tip": f"{y}: {fmt_eur(t)} · {fmt_int(year_counts[y])} viatges",
                }
                for y, t in year_totals.items()
            ],
            f"Despesa per any: {ambit}",
        )
        if len(year_totals) >= 2
        else None
    )
    totals = counted.groupby("persona_id")["total_eur"].sum().sort_values(ascending=False)
    people = counted.groupby("persona_id")["persona"].last().to_frame("persona")
    people_rows = category_rows(counted, totals.head(15).index, people, base)
    shares = category_shares(counted)
    return {
        "ambit": ambit,
        "noms": names,
        "shares": shares,
        "year_chart": year_chart,
        "people_rows": people_rows,
        "n_persones": counted["persona_id"].nunique(),
        "kpis": [
            ("Despesa total", fmt_eur(counted["total_eur"].sum())),
            ("Viatges", fmt_int(len(counted))),
            ("Alts càrrecs", fmt_int(counted["persona_id"].nunique())),
            ("Dies de viatge", fmt_int(counted["durada_dies"].sum())),
        ],
        "n_no_compten": len(trips) - len(counted),
    }


def _key_series(s: pd.Series) -> pd.Series:
    return s.map(_key)


ZERO_BADGES = {
    "imputat_a_altre": "Import imputat a un altre registre",
    "pagat_per_tercers": "Pagat per tercers",
    "pendent": "Import pendent",
    "sense_despesa": "Import 0",
}

FLAG_TEXTS = {
    "exclos_analisi": "Exclòs de l'anàlisi: la durada supera el percentil 99 i sol ser un "
    "error de data.",
    "flag_duplicat": "Duplicat d'un altre registre: no compta a les xifres.",
    "flag_possible_desdoblament": "Hi ha un altre registre de la mateixa persona i data amb "
    "un import diferent; pendent de revisar.",
    "flag_import_incomplet": "Falta alguna partida o el total.",
    "flag_import_inconsistent": "La suma de partides no coincideix amb el total.",
    "flag_redondeig": "La suma de partides difereix del total en pocs euros (arrodoniment).",
    "flag_no_estranger": "Totes les destinacions són a l'Estat espanyol.",
    "flag_tram_repetit": "La destinació publicada repeteix un tram amb un país incoherent.",
}
ZERO_TEXTS = {
    "imputat_a_altre": "Import 0: les despeses s'imputen al registre d'una altra persona.",
    "pagat_per_tercers": "Import 0: les despeses les va pagar un tercer.",
    "pendent": "Import 0: les dades econòmiques encara s'estaven gestionant.",
    "sense_despesa": "Import 0 sense explicació o sense despesa declarada.",
}


def trip_context(row: pd.Series, data: SiteData, base: str) -> dict:
    marks = [text for col, text in FLAG_TEXTS.items() if bool(row.get(col))]
    if isinstance(row.get("motiu_import_zero"), str):
        marks.append(ZERO_TEXTS[row["motiu_import_zero"]])
    notes = []
    for corr in data.correccions[data.correccions["id"] == row["id"]].itertuples():
        camp = "revisió" if corr.camp.startswith("revisio_") else corr.camp
        notes.append(
            {"camp": camp, "valor": corr.valor_nou, "motiu": corr.motiu, "font": corr.font}
        )
    names = country_names(data.trams)
    paisos = [names.get(i, i) for i in str(row.get("paisos_iso2") or "").split(";") if i]
    partides = [
        ("Dietes i manutenció", row["dietes_eur"]),
        ("Allotjament", row["allotjament_eur"]),
        ("Transport", row["transport_eur"]),
        ("Altres despeses", row["altres_despeses_eur"]),
    ]
    delay = row.get("dies_fins_publicacio")
    return {
        "v": row,
        "marks": marks,
        "notes": notes,
        "paisos": paisos,
        "partides": [(n, fmt_eur(x, 2)) for n, x in partides],
        "total": fmt_eur(row["total_eur"], 2),
        "inici": fmt_date(row["data_inici_iso"], long=True),
        "fi": fmt_date(row["data_fi_iso"], long=True),
        # Si la durada és anòmala, la data de fi no és fiable i el retard tampoc
        "delay": None if pd.isna(delay) or bool(row["exclos_analisi"]) else int(delay),
        "duplicat_de": row.get("duplicat_de") if bool(row.get("flag_duplicat")) else None,
    }


_URL = re.compile(r"https?://[^\s<>\"]+")


def linkify(value) -> Markup:
    """Escapa el text i converteix les URL en enllaços."""
    text = str(escape(text_or_none(value) or ""))
    return Markup(
        _URL.sub(lambda m: f'<a href="{m.group(0)}" rel="nofollow">{m.group(0)}</a>', text)
    )


def text_or_none(value) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    return text or None


# ---------------------------------------------------------------------------
# Construcció
# ---------------------------------------------------------------------------


def build_site(db_path: Path, manual_dir: Path, out_dir: Path, base: str = "/") -> Path:
    if not base.endswith("/"):
        base += "/"
    data = load(db_path, manual_dir)
    env = Environment(
        loader=FileSystemLoader(HERE / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(
        eur=fmt_eur, data=fmt_date, enter=fmt_int, text=text_or_none, enllacos=linkify
    )
    env.globals["categories"] = list(enumerate(label for _, label in CATEGORIES))
    updated = data.instantanies["downloaded_at"].iloc[-1]
    # Versió dels fitxers estàtics: canvia quan en canvia el contingut i evita que el
    # navegador continuï fent servir un CSS o JS antic de la memòria cau.
    digest = hashlib.sha256()
    for f in sorted((HERE / "static").iterdir()):
        digest.update(f.read_bytes())
    common = {
        "base": base,
        "versio": digest.hexdigest()[:10],
        "dataset_url": DATASET_URL,
        "repo_url": REPO_URL,
        "updated": fmt_date(updated, long=True),
    }

    tmp = out_dir.with_name(out_dir.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(HERE / "static", tmp)

    def render(template: str, path: str, **ctx) -> None:
        target = tmp / path
        target.parent.mkdir(parents=True, exist_ok=True)
        html = env.get_template(template).render(**common, **ctx)
        target.write_text(html, encoding="utf-8")

    render("inici.html", "index.html", page="inici", **home_context(data, base))
    render("viatges.html", "viatges/index.html", page="viatges")
    render("metodologia.html", "metodologia/index.html", page="metodologia",
           n_exclosos=int(data.viatges["exclos_analisi"].sum()),
           llindar=int(data.viatges.loc[data.viatges["exclos_analisi"], "durada_dies"].min() - 1)
           if data.viatges["exclos_analisi"].any() else None)  # fmt: skip
    render("404.html", "404.html", page=None)
    render("persones.html", "persones/index.html", page="persones", **people_context(data, base))
    render("departaments.html", "departaments/index.html", page="departaments",
           **departments_context(data, base))  # fmt: skip
    for ambit in data.viatges["ambit"].dropna().unique():
        render("departament.html", f"departament/{slug(ambit)}/index.html", page="departaments",
               **department_context(ambit, data, base))  # fmt: skip
    table = people_table(data)
    for pid in data.viatges["persona_id"].unique():
        render("persona.html", f"persona/{pid}/index.html", page="persones",
               **person_context(pid, data, table, base))  # fmt: skip
    for _, row in data.viatges.iterrows():
        render("viatge.html", f"viatge/{row['id']}/index.html", page="viatges",
               **trip_context(row, data, base))  # fmt: skip

    (tmp / "dades").mkdir(exist_ok=True)
    (tmp / "dades" / "viatges.json").write_text(
        json.dumps(explorer_payload(data), ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    data.viatges.to_csv(tmp / "dades" / "viatges.csv", index=False)
    data.trams.to_csv(tmp / "dades" / "trams.csv", index=False)

    shutil.rmtree(out_dir, ignore_errors=True)
    tmp.rename(out_dir)
    log.info("Web generat a %s (%d viatges)", out_dir, len(data.viatges))
    return out_dir
