import pandas as pd

from viatges.profiling import (
    build_inventory,
    load_snapshot,
    parse_amount,
    parse_date,
    placeholder_mask,
    render_report,
    run_profile,
    split_destinations,
)


def test_parse_amount():
    num, failed = parse_amount(pd.Series(["59.0", "1,5", "1.234,56", "", None, "o,oo"]))
    assert num.tolist()[:3] == [59.0, 1.5, 1234.56]
    assert failed.tolist() == [False, False, False, False, False, True]


def test_parse_date_accepta_iso_i_dmy():
    out, failed = parse_date(pd.Series(["22/09/2020", "2023-03-01T00:00:00.000", "32/13/2020"]))
    assert out[0] == pd.Timestamp("2020-09-22")
    assert out[1] == pd.Timestamp("2023-03-01")
    assert failed.tolist() == [False, False, True]


def test_placeholder_mask():
    s = pd.Series(["Cap", "-", "*", "Sense observacions.", None, "Director general", "0"])
    assert placeholder_mask(s).tolist() == [True, True, True, True, True, False, True]


def test_split_destinations():
    df = pd.DataFrame(
        {"id": ["a", "b"], "destinacio": ["Tokyo (Japó) / Kyoto (Japó)", "Brussel·les(Bèlgica)"]}
    )
    out = split_destinations(df)
    assert out["ciutat"].tolist() == ["Tokyo", "Kyoto", "Brussel·les"]
    assert out["pais"].tolist() == ["Japó", "Japó", "Bèlgica"]


def test_inventari_detecta_problemes(snapshot_dir):
    df, info = load_snapshot(snapshot_dir)
    assert info["missing_columns"] == []
    inv = build_inventory(df)
    assert inv["n_rows"] == 6
    assert inv["total_missing"] == 1
    assert set(inv["total_mismatch"]["id"]) == {"racc-X"}
    assert "racc-833, racc-834" in inv["shared_amounts"]["ids"].tolist()
    assert inv["n_multidesti"] == 2
    assert inv["trams_codificacio"].tolist() == ["Gda?sk (Polònia)"]
    assert "Perpinyà" in inv["trams_sense_pais"].index
    assert "Brussels" in inv["city_variants"]["variants"].iloc[0]
    assert inv["amount_parse_failures"]["transport"] == {"o,oo": 1}
    report = render_report(inv, info)
    assert "# Fase 0" in report


def test_run_profile_escriu_informe(snapshot_dir, tmp_path):
    out = run_profile(snapshot_dir, tmp_path / "reports")
    assert out.exists()
