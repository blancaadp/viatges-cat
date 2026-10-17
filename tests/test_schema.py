from viatges.schema import COLUMNS, field_mapping


def test_mapeja_pel_nom_visible_i_ignora_les_internes():
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
