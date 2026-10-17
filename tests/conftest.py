"""Fixtures amb registres reals del dataset (retallats), inclosos els seus problemes."""

import hashlib

import pandas as pd
import pytest

from viatges.ingest import _write_json
from viatges.prepare import Manual
from viatges.schema import COLUMNS

# fieldNames inventats a propòsit: el codi no ha de dependre de com els genera Socrata
FIELD_NAMES = {name: f"f_{i}" for i, name in enumerate(COLUMNS)}


def make_metadata() -> dict:
    cols = [{"name": n, "fieldName": f} for n, f in FIELD_NAMES.items()]
    cols.append({"name": "interna", "fieldName": ":id"})
    return {"columns": cols, "rowsUpdatedAt": 1_700_000_000}


def make_row(**values: str) -> dict:
    by_canonical = {v: FIELD_NAMES[k] for k, v in COLUMNS.items()}
    return {by_canonical[k]: v for k, v in values.items()}


ROWS = [
    # Normal; la suma quadra
    make_row(id="racc-493", departament="Acció Exterior", nom="Persona A",
             data_inici="22/09/2020", data_fi="23/09/2020", destinacio="Perpignan (França)",
             dietes="59.0", allotjament="103.00", transport="85.26", altres_despeses="0.00",
             total="247.26", comitiva="Cap", observacions="Cap"),
    # Diverses destinacions + import de transport compartit amb racc-834
    make_row(id="racc-833", departament="Empresa", nom="Persona B",
             data_inici="06/11/2022", data_fi="07/11/2022", destinacio="Kuala Lumpur (Malàisia)",
             dietes="20.08", allotjament="5605.08", transport="14298.80",
             altres_despeses="230.93", total="20154.89", comitiva="Cap de Gabinet",
             observacions="despeses conjuntes"),
    make_row(id="racc-834", departament="Empresa", nom="Persona B",
             data_inici="08/11/2022", data_fi="13/11/2022",
             destinacio="Tokyo (Japó) / Kyoto (Japó)", dietes="46.65", allotjament="5407.08",
             transport="14298.80", altres_despeses="0.00", total="19752.53", comitiva="*",
             observacions="-"),
    # Problema de codificació i sense espai abans del parèntesi
    make_row(id="racc-1050", departament="Justícia", nom="Persona C",
             data_inici="05/10/2023", data_fi="08/10/2023",
             destinacio="Gda?sk (Polònia) / Brussel·les(Bèlgica)", dietes="132.0",
             allotjament="420.00", transport="1438.87", altres_despeses="0.00",
             total="1990.87", comitiva="-", observacions="-"),
    # Total buit i destinació sense país
    make_row(id="ACC003", departament="Empresa", nom="Persona D",
             data_inici="12/01/2019", data_fi="17/01/2019", destinacio="Perpinyà",
             dietes="1000.00", allotjament="1345.00", transport="1326.88",
             altres_despeses="330.92", total="", comitiva="Cap", observacions=""),
    # Total que no quadra, import amb coma, variant de Brussel·les
    make_row(id="racc-X", departament="Cultura", nom="Persona E",
             data_inici="2023-03-01T00:00:00.000", data_fi="02/03/2023",
             destinacio="Brussels (Bèlgica)", dietes="10", allotjament="1,5",
             transport="o,oo", altres_despeses="0", total="50", comitiva="sense",
             observacions="Sense observacions."),
]  # fmt: skip


def write_snapshot(raw_dir, name: str, rows: list[dict], downloaded_at: str = "x"):
    """Escriu una instantània com les que deixa `viatges ingest` (mateix format i hash)."""
    d = raw_dir / name
    d.mkdir(parents=True)
    raw = _write_json(d / "rows.json", rows)
    _write_json(d / "metadata.json", make_metadata())
    manifest = {
        "downloaded_at": downloaded_at,
        "n_rows": len(rows),
        "sha256_rows": hashlib.sha256(raw).hexdigest(),
    }
    _write_json(d / "manifest.json", manifest)
    return d


@pytest.fixture
def snapshot_dir(tmp_path):
    return write_snapshot(tmp_path, "2026-01-01T000000Z", ROWS)


def frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows).astype("string")


@pytest.fixture
def manual() -> Manual:
    return Manual(
        paisos=frame(
            [
                {"variant": "Bèlgica", "pais": "Bèlgica", "iso2": "BE"},
                {"variant": "Polònia", "pais": "Polònia", "iso2": "PL"},
                {"variant": "Japó", "pais": "Japó", "iso2": "JP"},
                {"variant": "Malàisia", "pais": "Malàisia", "iso2": "MY"},
                {"variant": "Estats Units, els", "pais": "Estats Units", "iso2": "US"},
                {"variant": "Espanya", "pais": "Espanya", "iso2": "ES"},
                {"variant": "França", "pais": "França", "iso2": "FR"},
            ]
        ),
        ciutats=frame(
            [
                {"variant": "Brussels", "ciutat": "Brussel·les", "iso2": "BE"},
                {"variant": "Gda?sk", "ciutat": "Gdańsk", "iso2": "PL"},
                {"variant": "Tokyo", "ciutat": "Tòquio", "iso2": "JP"},
                {"variant": "Perpignan", "ciutat": "Perpinyà", "iso2": "FR"},
                {"variant": "Washington, D.C.", "ciutat": "Washington DC", "iso2": "US"},
                {"variant": "Madrid", "ciutat": "Madrid", "iso2": "ES"},
            ]
        ),
        departaments=frame(
            [
                {"departament": "Empresa", "ambit": "Empresa"},
                {"departament": "Cultura", "ambit": "Cultura"},
            ]
        ),
        correccions=frame(
            [
                {
                    "id": "racc-X",
                    "camp": "destinacio",
                    "valor_nou": "Brussels (Bèlgica)",
                    "motiu": "test",
                    "font": "test",
                }
            ]
        ),
    )
