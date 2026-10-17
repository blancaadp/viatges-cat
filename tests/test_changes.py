import pandas as pd
from conftest import ROWS, make_row, write_snapshot

from viatges.changes import compare_snapshots, run_changes


def test_compare_snapshots_detecta_altes_baixes_i_modificacions():
    old = pd.DataFrame(
        [
            {"id": "a", "total": "10", "observacions": None},
            {"id": "b", "total": "20", "observacions": "Cap"},
            {"id": "c", "total": "30", "observacions": "x"},
        ]
    )
    new = pd.DataFrame(
        [
            {"id": "a", "total": "10", "observacions": "Nova observació"},
            {"id": "b", "total": " 20 ", "observacions": "Cap"},  # només espais: no és canvi
            {"id": "d", "total": "40", "observacions": None},
        ]
    )
    changes = compare_snapshots(old, new)
    assert changes[["id", "tipus"]].values.tolist() == [
        ["d", "alta"],
        ["c", "baixa"],
        ["a", "modificacio"],
    ]
    mod = changes[changes["tipus"] == "modificacio"].iloc[0]
    assert mod["camp"] == "observacions"
    assert pd.isna(mod["valor_anterior"])
    assert mod["valor_nou"] == "Nova observació"


def test_buit_i_absent_compten_igual():
    old = pd.DataFrame([{"id": "a", "comitiva": ""}])
    new = pd.DataFrame([{"id": "a"}])
    assert compare_snapshots(old, new).empty


def test_columna_nova_amb_valor_es_una_modificacio():
    old = pd.DataFrame([{"id": "a"}])
    new = pd.DataFrame([{"id": "a", "nova": "valor"}])
    changes = compare_snapshots(old, new)
    assert changes[["camp", "valor_nou"]].values.tolist() == [["nova", "valor"]]


def test_run_changes_escriu_informe(tmp_path):
    raw = tmp_path / "raw"
    old = write_snapshot(raw, "2026-01-01T000000Z", ROWS[:2])
    extra = make_row(id="racc-NOU", nom="Persona F", destinacio="Roma (Itàlia)", total="1")
    new = write_snapshot(raw, "2026-01-08T000000Z", [*ROWS[:2], extra])
    out = run_changes(old, new, tmp_path / "reports")
    text = out.read_text(encoding="utf-8")
    assert out.name == "2026-01-08T000000Z.md"
    assert "Altes: **1**" in text
    assert "racc-NOU" in text
