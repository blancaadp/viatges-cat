import json

import pandas as pd
import pytest
from conftest import ROWS, write_snapshot

from viatges.site import (
    build_site,
    category_shares,
    column_chart,
    fmt_compact_eur,
    fmt_date,
    fmt_eur,
    linkify,
    person_sex,
)
from viatges.store import build_database


def test_format_catala():
    assert fmt_eur(1234567.891, 2) == "1.234.567,89 €"
    assert fmt_eur(float("nan")) == "—"
    assert fmt_compact_eur(1_255_443) == "1,3 M€"
    assert fmt_compact_eur(418_000) == "418 k€"
    assert fmt_date("2026-05-05", long=True) == "5 de maig de 2026"
    assert fmt_date("2026-04-17", long=True) == "17 d'abril de 2026"
    assert fmt_date(None) == "—"


def test_linkify_escapa_i_enllaca():
    html = str(linkify("Agenda: https://govern.cat/x?a=1 <b>"))
    assert '<a href="https://govern.cat/x?a=1"' in html
    assert "&lt;b&gt;" in html


def test_column_chart_te_zones_de_hover_i_etiqueta_el_maxim():
    svg = column_chart(
        [{"label": "2024", "value": 10, "tip": "a"}, {"label": "2025", "value": 30, "tip": "b"}],
        "Despesa",
    )
    assert svg.count('class="hit"') == 2
    assert svg.count('class="value"') == 1  # només el màxim porta etiqueta
    assert 'aria-label="Despesa"' in svg


@pytest.fixture
def site(tmp_path, manual, monkeypatch):
    raw = tmp_path / "raw"
    write_snapshot(raw, "2026-01-01T000000Z", ROWS, "2026-01-01T00:00:00+00:00")
    monkeypatch.setattr("viatges.store.load_manual", lambda _: manual)
    db = build_database(raw, tmp_path, tmp_path / "viatges.sqlite")
    manual_dir = tmp_path / "manual"
    manual_dir.mkdir()
    manual.correccions.to_csv(manual_dir / "correccions.csv", index=False)
    return build_site(db, manual_dir, tmp_path / "site", base="/viatges-cat")


def test_build_site_genera_totes_les_pagines(site):
    assert (site / "index.html").exists()
    assert (site / "viatges" / "index.html").exists()
    assert (site / "metodologia" / "index.html").exists()
    assert (site / "persones" / "index.html").exists()
    assert (site / "persona" / "persona-b" / "index.html").exists()
    assert len(list((site / "viatge").iterdir())) == len(ROWS)
    index = (site / "index.html").read_text(encoding="utf-8")
    assert 'href="/viatges-cat/estil.css?v=' in index  # amb versió per a la memòria cau
    assert "Despesa per any" in index


def test_dades_de_l_explorador(site):
    data = json.loads((site / "dades" / "viatges.json").read_text(encoding="utf-8"))
    assert len(data["rows"]) == len(ROWS)
    assert all(len(r) == len(data["columns"]) for r in data["rows"])
    assert data["paisos"]["BE"] == "Bèlgica"


def test_fitxa_mostra_la_nota_de_revisio(site):
    page = (site / "viatge" / "racc-X" / "index.html").read_text(encoding="utf-8")
    assert "Revisió manual" in page
    assert "Brussels (Bèlgica)" in page


def test_pagina_de_persones(site):
    page = (site / "persones" / "index.html").read_text(encoding="utf-8")
    assert 'role="tablist"' in page
    assert "/viatges-cat/persona/persona-b/" in page
    person = (site / "persona" / "persona-b" / "index.html").read_text(encoding="utf-8")
    assert "racc-833" in person and "racc-834" in person


def test_cercador_de_persones_inclou_variants_i_carrecs(site):
    page = (site / "persones" / "index.html").read_text(encoding="utf-8")
    assert 'id="cerca-persona"' in page
    assert 'data-cerca="persona b' in page  # nom en minúscules i sense accents
    home = (site / "index.html").read_text(encoding="utf-8")
    assert 'action="/viatges-cat/persones/"' in home


def test_category_shares_sumen_100():
    frame = pd.DataFrame(
        {
            "dietes_eur": [100.0, None],
            "allotjament_eur": [300.0, 100.0],
            "transport_eur": [500.0, 0.0],
            "altres_despeses_eur": [0.0, None],
        }
    )
    shares = category_shares(frame)
    assert shares["top"]["label"] == "Transport"
    assert [round(p["pct"]) for p in shares["parts"]] == [10, 40, 50, 0]
    assert sum(p["pct"] for p in shares["parts"]) == pytest.approx(100)
    assert category_shares(frame.iloc[0:0]) is None


def test_pagines_de_departaments_i_distribucio_per_persona(site):
    index = (site / "departaments" / "index.html").read_text(encoding="utf-8")
    assert "Distribució de la despesa per partida" in index
    departments = [p for p in (site / "departament").iterdir() if p.is_dir()]
    assert departments
    page = (departments[0] / "index.html").read_text(encoding="utf-8")
    assert "En què gasta" in page
    persona = (site / "persona" / "persona-b" / "index.html").read_text(encoding="utf-8")
    assert "En què gasta" in persona
    assert "En què gasta cada persona" in (site / "persones" / "index.html").read_text(
        encoding="utf-8"
    )


def test_sexe_estimat_pel_genere_del_carrec():
    v = pd.DataFrame(
        {
            "persona_id": ["a", "b", "c", "c", "d", "e"],
            "carrec": [
                "Consellera de Cultura",
                "director general d'Afers",
                "directora general",
                "director general",  # empat: queda sense classificar
                "gerent de la Fundació",  # neutre
                None,
            ],
        }
    )
    overrides = pd.DataFrame({"persona_id": ["d"], "sexe": ["home"], "motiu": ["x"]})
    sex = person_sex(v, overrides)
    assert sex["a"] == "Dones"
    assert sex["b"] == "Homes"
    assert pd.isna(sex["c"])
    assert sex["d"] == "Homes"  # la correcció manual preval
    assert pd.isna(sex["e"])


def test_pagina_de_destinacions_i_sense_sexe_si_no_es_pot_estimar(site):
    page = (site / "destinacions" / "index.html").read_text(encoding="utf-8")
    assert "Destinacions" in page
    assert 'class="data split sortable"' in page
    persones = (site / "persones" / "index.html").read_text(encoding="utf-8")
    # Sense càrrecs amb gènere no es pot estimar el sexe: la secció no es mostra
    assert 'id="sexe"' not in persones
