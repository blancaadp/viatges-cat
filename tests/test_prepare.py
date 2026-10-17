import pandas as pd
import pytest
from conftest import frame

from viatges.prepare import (
    annotate_corrections,
    build_trams,
    classify_zero_total,
    mark_duplicates,
    normalize_place,
    parse_amounts,
    parse_dates,
    prepare,
    run_prepare,
    split_trams,
)
from viatges.profiling import load_snapshot


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Tokyo (Japó) / Kyoto (Japó)", ["Tokyo (Japó)", "Kyoto (Japó)"]),
        ("Tànger (Marrroc) i Rabat (Marroc)", ["Tànger (Marrroc)", "Rabat (Marroc)"]),
        ("Buenos Aires (Argentina) Montevideo (Uruguai)",
         ["Buenos Aires (Argentina)", "Montevideo (Uruguai)"]),
        ("Washington, D.C. (Estats Units, els)", ["Washington, D.C. (Estats Units, els)"]),
        ('Oliena (Sardenya, Itàlia)"', ["Oliena (Sardenya, Itàlia)"]),
        ("Bratislava (Eslovàquia).", ["Bratislava (Eslovàquia)"]),
        ('"Brussel·les (Bèlgica)', ["Brussel·les (Bèlgica)"]),
        ("Maputo (Moçambic)/Inhambane (Moçambic)", ["Maputo (Moçambic)", "Inhambane (Moçambic)"]),
        ("Madrid", ["Madrid"]),
    ],
)  # fmt: skip
def test_split_trams(raw, expected):
    assert split_trams(raw) == expected


def test_normalize_place():
    assert normalize_place("BRUSSEL·LES") == "Brussel·les"
    assert normalize_place("Brussel.les ") == "Brussel·les"
    assert normalize_place("  Andorra  la Vella. ") == "Andorra la Vella"
    assert normalize_place(None) is None


def test_classify_zero_total():
    obs = pd.Series(
        [
            "Les despeses del viatge s'imputen al registre del viatge del MHP",
            "Despeses assumides per l'Incasol",
            "Informació econòmica en curs d'elaboració",
            "Cap",
            None,
        ]
    )
    assert classify_zero_total(obs).tolist() == [
        "imputat_a_altre",
        "pagat_per_tercers",
        "pendent",
        "sense_despesa",
        "sense_despesa",
    ]


def amounts(**overrides) -> dict:
    base = {
        "dietes": "10",
        "allotjament": "20",
        "transport": "30",
        "altres_despeses": "0",
        "total": "60",
        "observacions": "",
    }
    return {**base, **overrides}


def test_parse_amounts_conserva_els_valors_publicats():
    df = frame(
        [
            amounts(),  # quadra
            amounts(total=""),  # total buit: no s'omple
            amounts(total="62"),  # arrodoniment tolerable
            amounts(total="100"),  # inconsistent
            amounts(altres_despeses="", total=""),  # incomplet: no s'inventa
            amounts(
                dietes="0",
                allotjament="0",
                transport="0",
                total="0",
                observacions="Les dades econòmiques s'estan gestionant",
            ),  # fmt: skip
        ]
    )
    out = parse_amounts(df)
    assert out["total_eur"].iloc[[0, 2, 3]].tolist() == [60, 62, 100]
    assert pd.isna(out["total_eur"].iloc[1])
    assert out["flag_redondeig"].tolist() == [False, False, True, False, False, False]
    assert out["flag_import_inconsistent"].tolist() == [False, False, False, True, False, False]
    assert out["flag_import_incomplet"].tolist() == [False, True, False, False, True, False]
    # un total pendent es marca però es conserva tal com ve (0)
    assert out["motiu_import_zero"].iloc[5] == "pendent"
    assert out["total_eur"].iloc[5] == 0


def test_parse_dates_exclou_nomes_per_sobre_del_p99():
    short = [{"data_inici": "22/09/2020", "data_fi": "23/09/2020"}] * 199
    long = {"data_inici": "2024-04-17T00:00:00.000", "data_fi": "2024-09-19T00:00:00.000"}
    out = parse_dates(frame([*short, long]))
    assert out["durada_dies"].iloc[-1] == 156
    assert out["data_fi_iso"].iloc[-1].isoformat() == "2024-09-19"  # la data no es corregeix
    assert out["exclos_analisi"].tolist() == [False] * 199 + [True]


def test_mark_duplicates():
    df = pd.DataFrame(
        {
            "id": ["CMH020", "racc-31", "racc-1036", "racc-1053", "racc-1"],
            "nom": ["Ernest M", "Ernest  M", "Carme P", "Carme P", "Altra"],
            "data_inici_iso": ["2018-07-14"] * 2 + ["2023-11-13"] * 2 + ["2023-11-13"],
            "total_eur": [14298.23, 14298.23, 684.92, 724.92, 10.0],
        }
    )
    out = mark_duplicates(df).set_index("id")
    # el registre racc té prioritat sobre el CMH
    assert out.loc["CMH020", "flag_duplicat"]
    assert out.loc["CMH020", "duplicat_de"] == "racc-31"
    assert not out.loc["racc-31", "flag_duplicat"]
    # mateix viatge amb imports diferents: s'agrupa però no es descarta
    assert out.loc[["racc-1036", "racc-1053"], "flag_possible_desdoblament"].all()
    assert set(out.loc[["racc-1036", "racc-1053"], "grup_viatge"]) == {"racc-1036"}
    assert not out.loc["racc-1", "flag_possible_desdoblament"]


def test_build_trams(manual):
    df = pd.DataFrame(
        {
            "id": ["a", "b", "c", "d"],
            "destinacio": [
                "Gda?sk (Polònia) / Brussels(Bèlgica)",
                "Japó",
                "Washington, D.C. (Estats Units, els)",
                "Perpignan",
            ],
        }
    )
    trams = build_trams(df, manual)
    ciutats = [None if pd.isna(c) else c for c in trams["ciutat"]]
    assert ciutats == ["Gdańsk", "Brussel·les", None, "Washington DC", "Perpinyà"]
    assert trams["iso2"].tolist() == ["PL", "BE", "JP", "US", "FR"]
    assert trams["pais"].tolist()[-1] == "França"


def test_build_trams_no_forca_una_ciutat_d_un_altre_pais(manual):
    trams = build_trams(pd.DataFrame({"id": ["a"], "destinacio": ["Tokyo (França)"]}), manual)
    assert trams["ciutat"].tolist() == ["Tokyo"]
    assert not trams["ciutat_mapejada"].iloc[0]
    assert trams["iso2"].tolist() == ["FR"]


def test_annotate_corrections_no_modifica_el_valor_publicat(manual):
    df = pd.DataFrame({"id": ["racc-X", "altre"], "destinacio": ["Brussel·les", "Roma"]})
    out = annotate_corrections(df, manual.correccions)
    assert out["destinacio"].tolist() == ["Brussel·les", "Roma"]
    assert out["correccio_destinacio"].iloc[0] == "Brussels (Bèlgica)"
    assert pd.isna(out["correccio_destinacio"].iloc[1])
    assert out["correccions"].tolist()[0] == "destinacio"
    assert pd.isna(out["correccions"].iloc[1])


def test_prepare_sobre_la_fixture(snapshot_dir, manual):
    df, _ = load_snapshot(snapshot_dir)
    viatges, trams = prepare(df, manual)
    v = viatges.set_index("id")
    assert len(viatges) == 6
    assert pd.isna(v.loc["ACC003", "total_eur"])  # el total buit no s'omple
    assert v.loc["ACC003", "flag_import_incomplet"]
    assert v.loc["racc-834", "n_trams"] == 2
    assert v.loc["racc-1050", "paisos_iso2"] == "PL;BE"
    assert v.loc["racc-833", "ambit"] == "Empresa"
    assert v.loc["racc-X", "destinacio"] == "Brussels (Bèlgica)"  # tal com ve
    assert not viatges.filter(like="_clean").columns.any()


def test_run_prepare_escriu_les_sortides(snapshot_dir, manual, tmp_path, monkeypatch):
    monkeypatch.setattr("viatges.prepare.load_manual", lambda _: manual)
    out = run_prepare(snapshot_dir, tmp_path, tmp_path / "processed", tmp_path / "reports")
    assert (out / "viatges.csv").exists()
    assert (out / "trams.csv").exists()
    report = (tmp_path / "reports" / "fase1_preparacio.md").read_text(encoding="utf-8")
    assert "# Fase 1" in report


def test_mark_duplicates_respecta_la_revisio_manual():
    df = pd.DataFrame(
        {
            "id": ["racc-1036", "racc-1053", "racc-72", "racc-80", "racc-757", "racc-758",
                   "e-1", "e-2"],
            "nom": ["Carme P"] * 2 + ["Javier F"] * 2 + ["Gerard F"] * 2 + ["Elisabet C"] * 2,
            "data_inici_iso": ["2023-11-13"] * 2 + ["2018-11-22"] * 2 + ["2022-09-28"] * 2
            + ["2026-05-19"] * 2,
            "total_eur": [684.92, 724.92, 902.09, 183.39, 601.96, 923.17, 1657.8, 1371.03],
            "revisio_duplicat_de": ["racc-1053"] + [pd.NA] * 7,
            "revisio_desdoblament": [pd.NA, pd.NA, "independent", "independent",
                                     "complementari", "complementari", "pendent", "pendent"],
        }
    )  # fmt: skip
    out = mark_duplicates(df).set_index("id")
    # duplicat manual: es conserva el més recent, que passa a encapçalar el grup
    assert out.loc["racc-1036", "flag_duplicat"]
    assert out.loc["racc-1036", "duplicat_de"] == "racc-1053"
    assert set(out.loc[["racc-1036", "racc-1053"], "grup_viatge"]) == {"racc-1053"}
    # independents: cadascun el seu grup
    assert out.loc["racc-80", "grup_viatge"] == "racc-80"
    # complementaris: un grup i resolt
    assert set(out.loc[["racc-757", "racc-758"], "grup_viatge"]) == {"racc-757"}
    assert not out.loc[["racc-72", "racc-757", "racc-1053"], "flag_possible_desdoblament"].any()
    # pendent: continua marcat
    assert out.loc[["e-1", "e-2"], "flag_possible_desdoblament"].all()


def test_mark_duplicates_rebutja_decisions_desconegudes():
    df = pd.DataFrame(
        {"id": ["a"], "nom": ["X"], "data_inici_iso": ["2020-01-01"], "total_eur": [1.0],
         "revisio_desdoblament": ["potser"]}
    )  # fmt: skip
    with pytest.raises(ValueError, match="potser"):
        mark_duplicates(df)


def test_build_trams_descarta_el_tram_repetit_consecutiu(manual):
    df = pd.DataFrame(
        {
            "id": ["a", "b"],
            "destinacio": [
                "Tokyo (Japó)Tokyo (França)",
                "Tokyo (Japó) / Perpignan / Tokyo (Japó)",
            ],
        }
    )
    trams = build_trams(df, manual)
    assert trams.loc[trams["id"] == "a", "iso2"].tolist() == ["JP"]
    # una tornada a la mateixa ciutat, no consecutiva, es conserva
    assert trams.loc[trams["id"] == "b", "ciutat"].tolist() == ["Tòquio", "Perpinyà", "Tòquio"]
