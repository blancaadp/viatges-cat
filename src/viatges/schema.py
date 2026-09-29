"""Esquema esperado del dataset y traducción de los nombres de la API a nombres canónicos.

La API devuelve `fieldName` generados por Socrata (sin acentos, a veces truncados).
En lugar de adivinarlos, los mapeamos a partir del nombre visible de cada columna
que aparece en los metadatos. Si el portal cambia el esquema, lo detectamos aquí.
"""

from __future__ import annotations

import unicodedata
from typing import Any

# Nombre visible en el portal -> nombre canónico en nuestro código
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
    """Normaliza un nombre para compararlo (Unicode NFC, espacios, mayúsculas)."""
    return " ".join(unicodedata.normalize("NFC", name).split()).casefold()


_EXPECTED = {_key(k): v for k, v in COLUMNS.items()}


def field_mapping(metadata: dict[str, Any]) -> tuple[dict[str, str], list[str], list[str]]:
    """Devuelve (fieldName -> canónico, columnas inesperadas, columnas esperadas que faltan)."""
    mapping: dict[str, str] = {}
    unexpected: list[str] = []
    for col in metadata.get("columns", []):
        field, name = col.get("fieldName", ""), col.get("name", "")
        if not field or field.startswith(":"):  # columnas internas de Socrata
            continue
        canonical = _EXPECTED.get(_key(name))
        if canonical:
            mapping[field] = canonical
        else:
            unexpected.append(name)
    missing = sorted(set(COLUMNS.values()) - set(mapping.values()))
    return mapping, unexpected, missing
