from viatges.schema import COLUMNS, field_mapping


def test_mapea_por_nombre_visible_e_ignora_internas():
    meta = {
        "columns": [
            {"name": "Unitat  orgànica", "fieldName": "unitat_org_nica"},
            {"name": "Nova columna", "fieldName": "nova"},
            {"name": "x", "fieldName": ":updated_at"},
        ]
    }
    mapping, unexpected, missing = field_mapping(meta)
    assert mapping == {"unitat_org_nica": "unitat_organica"}
    assert unexpected == ["Nova columna"]
    assert len(missing) == len(COLUMNS) - 1
