import json

import pytest
from conftest import ROWS, write_snapshot

from viatges.site import build_site, column_chart, fmt_compact_eur, fmt_date, fmt_eur, linkify
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
