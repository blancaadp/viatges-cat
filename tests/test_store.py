import sqlite3

import pandas as pd
import pytest
from conftest import ROWS, make_row, write_snapshot

from viatges.store import build_database


@pytest.fixture
def raw_dir(tmp_path):
    raw = tmp_path / "raw"
    write_snapshot(raw, "2026-01-01T000000Z", ROWS, "2026-01-01T00:00:00+00:00")
    changed = [dict(r) for r in ROWS[1:]]  # racc-493 desapareix
    late = make_row(id="racc-TARD", departament="Cultura", nom="Persona F",
                    data_inici="01/01/2026", data_fi="03/01/2026",
                    destinacio="Roma (Itàlia)", dietes="1", allotjament="1",
                    transport="1", altres_despeses="0", total="3")  # fmt: skip
    write_snapshot(raw, "2026-01-21T000000Z", [*changed, late], "2026-01-21T00:00:00+00:00")
    return raw


def test_build_database(raw_dir, manual, tmp_path, monkeypatch):
    monkeypatch.setattr("viatges.store.load_manual", lambda _: manual)
    db = build_database(raw_dir, tmp_path, tmp_path / "viatges.sqlite")

    with sqlite3.connect(db) as con:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert tables == {"instantanies", "viatges", "trams", "canvis", "historial_ids"}
        canvis = pd.read_sql("SELECT id, tipus FROM canvis WHERE tipus != 'modificacio'", con)
        historial = pd.read_sql("SELECT * FROM historial_ids", con).set_index("id")
        viatges = pd.read_sql("SELECT * FROM viatges", con).set_index("id")

    assert sorted(canvis.values.tolist()) == [["racc-493", "baixa"], ["racc-TARD", "alta"]]
    assert not historial.loc["racc-493", "vigent"]
    assert historial.loc["racc-TARD", "primera_instantania"] == "2026-01-21T000000Z"
    # els viatges són els de la darrera instantània
    assert "racc-493" not in viatges.index
    # retard: conegut només per als que apareixen després de la primera instantània
    assert viatges.loc["racc-TARD", "dies_fins_publicacio"] == 18
    assert pd.isna(viatges.loc["racc-833", "dies_fins_publicacio"])


def test_build_database_sense_instantanies(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_database(tmp_path / "buit", tmp_path, tmp_path / "db.sqlite")
