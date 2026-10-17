import pandas as pd
import pytest

from viatges.clean import (
    Manual,
    apply_corrections,
    build_trams,
    classify_zero_total,
    clean,
    clean_amounts,
    clean_dates,
    mark_duplicates,
    normalize_place,
    run_clean,
    split_trams,
)
from viatges.profiling import load_snapshot


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
                {"departament": "Empresa", "departament_clean": "Empresa", "ambit": "Empresa"},
                {"departament": "Cultura", "departament_clean": "Cultura", "ambit": "Cultura"},
            ]
        ),
        correcciones=frame(
            [
                {
                    "id": "racc-X",
                    "campo": "destinacio",
                    "valor_nuevo": "Brussels (Bèlgica)",
                    "motivo": "test",
                    "fuente": "test",
                }
            ]
        ),
    )


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


def test_clean_amounts():
    df = frame(
        [
            amounts(),  # cuadra
            amounts(total=""),  # total calculado
            amounts(total="62"),  # redondeo tolerable
            amounts(total="100"),  # inconsistente
            amounts(altres_despeses="", total=""),  # incompleto: no se inventa
            amounts(
                dietes="0",
                allotjament="0",
                transport="0",
                total="0",
                observacions="Les dades econòmiques s'estan gestionant",
            ),  # fmt: skip
        ]
    )
    out = clean_amounts(df)
    assert out["total_clean"].tolist()[:4] == [60, 60, 62, 100]
    assert out["flag_total_calculat"].tolist() == [False, True, False, False, False, False]
    assert out["flag_redondeig"].tolist() == [False, False, True, False, False, False]
    assert out["flag_import_inconsistent"].tolist() == [False, False, False, True, False, False]
    assert out["flag_import_incomplet"].tolist() == [False, False, False, False, True, True]
    assert out["motiu_import_zero"].iloc[5] == "pendent"
    assert pd.isna(out["total_clean"].iloc[5])


def test_clean_dates_marca_viajes_largos():
    df = frame(
        [
            {"data_inici": "22/09/2020", "data_fi": "23/09/2020"},
            {"data_inici": "2024-04-17T00:00:00.000", "data_fi": "2024-09-19T00:00:00.000"},
        ]
    )
    out = clean_dates(df)
    assert out["durada_dies"].tolist() == [2, 156]
    assert out["flag_durada_sospitosa"].tolist() == [False, True]


def test_mark_duplicates():
    df = pd.DataFrame(
        {
            "id": ["CMH020", "racc-31", "racc-1036", "racc-1053", "racc-1"],
            "nom": ["Ernest M", "Ernest  M", "Carme P", "Carme P", "Altra"],
            "data_inici_clean": ["2018-07-14"] * 2 + ["2023-11-13"] * 2 + ["2023-11-13"],
            "total_clean": [14298.23, 14298.23, 684.92, 724.92, 10.0],
        }
    )
    out = mark_duplicates(df).set_index("id")
    # el registro racc tiene prioridad sobre el CMH
    assert out.loc["CMH020", "flag_duplicat"]
    assert out.loc["CMH020", "duplicat_de"] == "racc-31"
    assert not out.loc["racc-31", "flag_duplicat"]
    # mismo viaje con importes distintos: se agrupa pero no se descarta
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


def test_build_trams_no_fuerza_una_ciudad_de_otro_pais(manual):
    trams = build_trams(pd.DataFrame({"id": ["a"], "destinacio": ["Tokyo (França)"]}), manual)
    assert trams["ciutat"].tolist() == ["Tokyo"]
    assert not trams["ciutat_mapejada"].iloc[0]
    assert trams["iso2"].tolist() == ["FR"]


def test_apply_corrections(manual):
    df = pd.DataFrame({"id": ["racc-X", "otro"], "destinacio": ["Brussel·les", "Roma"]})
    out = apply_corrections(df, manual.correcciones)
    assert out["destinacio"].tolist() == ["Brussels (Bèlgica)", "Roma"]
    assert out["correccions"].tolist()[0] == "destinacio"
    assert pd.isna(out["correccions"].iloc[1])


def test_clean_sobre_fixture(snapshot_dir, manual):
    df, _ = load_snapshot(snapshot_dir)
    viatges, trams = clean(df, manual)
    v = viatges.set_index("id")
    assert len(viatges) == 6
    assert v.loc["ACC003", "total_clean"] == pytest.approx(4002.80)
    assert v.loc["racc-834", "n_trams"] == 2
    assert v.loc["racc-1050", "paisos_iso2"] == "PL;BE"
    assert pd.isna(v.loc["racc-834", "comitiva_clean"])  # "*" es relleno
    assert v.loc["racc-833", "comitiva_clean"] == "Cap de Gabinet"
    assert v.loc["racc-833", "ambit"] == "Empresa"


def test_run_clean_escribe_salidas(snapshot_dir, manual, tmp_path, monkeypatch):
    monkeypatch.setattr("viatges.clean.load_manual", lambda _: manual)
    out = run_clean(snapshot_dir, tmp_path, tmp_path / "processed", tmp_path / "reports")
    assert (out / "viatges.csv").exists()
    assert (out / "trams.csv").exists()
    assert "# Fase 1" in (tmp_path / "reports" / "fase1_neteja.md").read_text(encoding="utf-8")


def test_mark_duplicates_respeta_la_revision_manual():
    df = pd.DataFrame(
        {
            "id": ["racc-1036", "racc-1053", "racc-72", "racc-80", "racc-757", "racc-758",
                   "e-1", "e-2"],
            "nom": ["Carme P"] * 2 + ["Javier F"] * 2 + ["Gerard F"] * 2 + ["Elisabet C"] * 2,
            "data_inici_clean": ["2023-11-13"] * 2 + ["2018-11-22"] * 2 + ["2022-09-28"] * 2
            + ["2026-05-19"] * 2,
            "total_clean": [684.92, 724.92, 902.09, 183.39, 601.96, 923.17, 1657.8, 1371.03],
            "revisio_duplicat_de": ["racc-1053"] + [pd.NA] * 7,
            "revisio_desdoblament": [pd.NA, pd.NA, "independent", "independent",
                                     "complementari", "complementari", "pendent", "pendent"],
        }
    )  # fmt: skip
    out = mark_duplicates(df).set_index("id")
    # duplicado manual: se conserva el más reciente, que pasa a encabezar el grupo
    assert out.loc["racc-1036", "flag_duplicat"]
    assert out.loc["racc-1036", "duplicat_de"] == "racc-1053"
    assert set(out.loc[["racc-1036", "racc-1053"], "grup_viatge"]) == {"racc-1053"}
    # independientes: cada uno su grupo
    assert out.loc["racc-80", "grup_viatge"] == "racc-80"
    # complementarios: un grupo y resuelto
    assert set(out.loc[["racc-757", "racc-758"], "grup_viatge"]) == {"racc-757"}
    assert not out.loc[["racc-72", "racc-757", "racc-1053"], "flag_possible_desdoblament"].any()
    # pendiente: sigue marcado
    assert out.loc[["e-1", "e-2"], "flag_possible_desdoblament"].all()


def test_mark_duplicates_rechaza_decisiones_desconocidas():
    df = pd.DataFrame(
        {"id": ["a"], "nom": ["X"], "data_inici_clean": ["2020-01-01"], "total_clean": [1.0],
         "revisio_desdoblament": ["quizas"]}
    )  # fmt: skip
    with pytest.raises(ValueError, match="quizas"):
        mark_duplicates(df)
