"""Esquema esperat del dataset i traducció dels noms de l'API a noms canònics.

L'API retorna `fieldName` generats per Socrata (sense accents, de vegades truncats).
En lloc d'endevinar-los, els mapegem a partir del nom visible de cada columna
que apareix a les metadades. Si el portal canvia l'esquema, ho detectem aquí.
"""

from __future__ import annotations

import unicodedata
from typing import Any

# Nom visible al portal -> nom canònic al nostre codi
COLUMNS: dict[str, str] = {
    "Id": "id",
    "Departament": "departament",
    "Unitat orgànica": "unitat_organica",
    "Nom i cognoms": "nom",
    "Càrrec": "carrec",
    "Inici viatge": "data_inici",
    "Fi viatge": "data_fi",
    "Destinació": "destinacio",
    "Motiu": "motiu",
    "Agenda": "agenda",
    "Comitiva": "comitiva",
    "Dietes i manutenció": "dietes",
    "Allotjament": "allotjament",
    "Transport": "transport",
    "Altres despeses": "altres_despeses",
    "Total despeses": "total",
    "Especificació altres despeses": "altres_despeses_detall",
    "Observacions": "observacions",
}

COST_COLUMNS = ["dietes", "allotjament", "transport", "altres_despeses"]
AMOUNT_COLUMNS = [*COST_COLUMNS, "total"]
DATE_COLUMNS = ["data_inici", "data_fi"]


def _key(name: str) -> str:
    """Normalitza un nom per comparar-lo (Unicode NFC, espais, majúscules)."""
    return " ".join(unicodedata.normalize("NFC", name).split()).casefold()


_EXPECTED = {_key(k): v for k, v in COLUMNS.items()}


def field_mapping(metadata: dict[str, Any]) -> tuple[dict[str, str], list[str], list[str]]:
    """Retorna (fieldName -> canònic, columnes inesperades, columnes esperades que falten)."""
    mapping: dict[str, str] = {}
    unexpected: list[str] = []
    for col in metadata.get("columns", []):
        field, name = col.get("fieldName", ""), col.get("name", "")
        if not field or field.startswith(":"):  # columnes internes de Socrata
            continue
        canonical = _EXPECTED.get(_key(name))
        if canonical:
            mapping[field] = canonical
        else:
            unexpected.append(name)
    missing = sorted(set(COLUMNS.values()) - set(mapping.values()))
    return mapping, unexpected, missing
