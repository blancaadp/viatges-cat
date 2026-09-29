"""Fixtures con registros reales del dataset (recortados), incluidos sus problemas."""

import json

import pytest

from viatges.schema import COLUMNS

# fieldNames inventados a propósito: el código no debe depender de cómo los genere Socrata
FIELD_NAMES = {name: f"f_{i}" for i, name in enumerate(COLUMNS)}


def make_metadata() -> dict:
    cols = [{"name": n, "fieldName": f} for n, f in FIELD_NAMES.items()]
    cols.append({"name": "interna", "fieldName": ":id"})
    return {"columns": cols, "rowsUpdatedAt": 1_700_000_000}


def make_row(**values: str) -> dict:
    by_canonical = {v: FIELD_NAMES[k] for k, v in COLUMNS.items()}
    return {by_canonical[k]: v for k, v in values.items()}


ROWS = [
    # Normal; suma cuadra
    make_row(id="racc-493", departament="Acció Exterior", nom="Persona A",
             data_inici="22/09/2020", data_fi="23/09/2020", destinacio="Perpignan (França)",
             dietes="59.0", allotjament="103.00", transport="85.26", altres_despeses="0.00",
             total="247.26", comitiva="Cap", observacions="Cap"),
    # Varios destinos + importe de transporte compartido con racc-834
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
    # Problema de codificación y sin espacio antes del paréntesis
    make_row(id="racc-1050", departament="Justícia", nom="Persona C",
             data_inici="05/10/2023", data_fi="08/10/2023",
             destinacio="Gda?sk (Polònia) / Brussel·les(Bèlgica)", dietes="132.0",
             allotjament="420.00", transport="1438.87", altres_despeses="0.00",
             total="1990.87", comitiva="-", observacions="-"),
    # Total vacío y destino sin país
    make_row(id="ACC003", departament="Empresa", nom="Persona D",
             data_inici="12/01/2019", data_fi="17/01/2019", destinacio="Perpinyà",
             dietes="1000.00", allotjament="1345.00", transport="1326.88",
             altres_despeses="330.92", total="", comitiva="Cap", observacions=""),
    # Total que no cuadra, importe con coma, variante de Bruselas
    make_row(id="racc-X", departament="Cultura", nom="Persona E",
             data_inici="2023-03-01T00:00:00.000", data_fi="02/03/2023",
             destinacio="Brussels (Bèlgica)", dietes="10", allotjament="1,5",
             transport="o,oo", altres_despeses="0", total="50", comitiva="sense",
             observacions="Sense observacions."),
]  # fmt: skip


@pytest.fixture
def snapshot_dir(tmp_path):
    d = tmp_path / "2026-01-01T000000Z"
    d.mkdir()
    (d / "rows.json").write_text(json.dumps(ROWS), encoding="utf-8")
    (d / "metadata.json").write_text(json.dumps(make_metadata()), encoding="utf-8")
    (d / "manifest.json").write_text(json.dumps({"downloaded_at": "x"}), encoding="utf-8")
    return d
