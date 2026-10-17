"""Tests de la còpia a Turso contra un servidor simulat que parla el protocol `/v2/pipeline`
i executa l'SQL en un SQLite en memòria."""

import json
import sqlite3

import httpx
import pytest
from conftest import ROWS, make_row, write_snapshot

from viatges.store import build_database
from viatges.turso import (
    TursoClient,
    TursoError,
    decode_value,
    encode_value,
    insert_statements,
    pull,
    push,
)


class FakeTurso:
    def __init__(self) -> None:
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.requests = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v2/pipeline"
        assert request.headers["Authorization"] == "Bearer secret"
        self.requests += 1
        results = []
        for req in json.loads(request.content)["requests"]:
            if req["type"] == "close":
                results.append({"type": "ok", "response": {"type": "close"}})
                continue
            stmt = req["stmt"]
            args = [decode_value(a) for a in stmt.get("args", [])]
            try:
                cursor = self.db.execute(stmt["sql"], args)
            except sqlite3.Error as exc:
                results.append({"type": "error", "error": {"message": str(exc)}})
                continue
            cols = [{"name": d[0]} for d in cursor.description or []]
            rows = [[encode_value(v) for v in row] for row in cursor.fetchall()]
            result = {"cols": cols, "rows": rows, "affected_row_count": cursor.rowcount}
            results.append({"type": "ok", "response": {"type": "execute", "result": result}})
        return httpx.Response(200, json={"baton": None, "results": results})

    def client(self) -> TursoClient:
        return TursoClient(
            "libsql://viatges-test.turso.io", "secret", transport=httpx.MockTransport(self.handler)
        )


@pytest.mark.parametrize("value", [None, True, 42, 1.5, "text amb accents: Lió", b"\x00\x01"])
def test_encode_decode_roundtrip(value):
    expected = int(value) if isinstance(value, bool) else value
    assert decode_value(encode_value(value)) == expected


def test_nan_es_null():
    assert encode_value(float("nan")) == {"type": "null"}


def test_insert_statements_respecta_el_limit_d_arguments():
    rows = [(i, "x") for i in range(1000)]
    statements = list(insert_statements("t", ["a", "b"], rows))
    assert all(len(args) <= 900 for _, args in statements)
    assert sum(len(args) for _, args in statements) == 2000


def test_query_i_errors():
    fake = FakeTurso()
    with fake.client() as client:
        client.execute([("CREATE TABLE t (a INTEGER, b TEXT)", [])])
        client.execute([("INSERT INTO t VALUES (?, ?)", [1, "u"])])
        assert client.query("SELECT * FROM t") == [{"a": 1, "b": "u"}]
        with pytest.raises(TursoError, match="no such table"):
            client.query("SELECT * FROM no_existeix")


@pytest.fixture
def local(tmp_path, manual, monkeypatch):
    raw = tmp_path / "raw"
    write_snapshot(raw, "2026-01-01T000000Z", ROWS, "2026-01-01T00:00:00+00:00")
    late = make_row(id="racc-TARD", departament="Cultura", nom="Persona F",
                    data_inici="01/01/2026", data_fi="03/01/2026",
                    destinacio="Roma (Itàlia)", total="3")  # fmt: skip
    write_snapshot(raw, "2026-01-21T000000Z", [*ROWS, late], "2026-01-21T00:00:00+00:00")
    monkeypatch.setattr("viatges.store.load_manual", lambda _: manual)
    db = build_database(raw, tmp_path, tmp_path / "viatges.sqlite")
    return raw, db


def test_push_i_pull_reconstrueixen_les_instantanies(local, tmp_path):
    raw, db = local
    fake = FakeTurso()
    with fake.client() as client:
        push(client, raw, db)
        assert client.query("SELECT COUNT(*) AS n FROM viatges") == [{"n": 7}]
        assert client.query("SELECT COUNT(*) AS n FROM arxiu_instantanies") == [{"n": 2}]
        tables = {r["name"] for r in client.query("SELECT name FROM sqlite_master")}
        assert not any(t.startswith("_nou_") for t in tables)
        assert "idx_trams_id" in tables

        restored = tmp_path / "restaurat"
        new = pull(client, restored)

    assert [p.name for p in new] == ["2026-01-01T000000Z", "2026-01-21T000000Z"]
    for name in ["2026-01-01T000000Z", "2026-01-21T000000Z"]:
        for file in ["rows.json", "manifest.json", "metadata.json"]:
            assert (restored / name / file).read_bytes() == (raw / name / file).read_bytes()


def test_push_es_idempotent_i_nomes_puja_el_que_falta(local):
    raw, db = local
    fake = FakeTurso()
    with fake.client() as client:
        push(client, raw, db)
        push(client, raw, db)
        assert client.query("SELECT COUNT(*) AS n FROM arxiu_files") == [{"n": 13}]
        assert client.query("SELECT COUNT(*) AS n FROM trams")[0]["n"] > 0


def test_pull_detecta_un_arxiu_corrupte(local, tmp_path):
    raw, db = local
    fake = FakeTurso()
    with fake.client() as client:
        push(client, raw, db)
        client.execute([('UPDATE arxiu_files SET fila_json = \'{"id": "x"}\' WHERE ordre = 0', [])])
        with pytest.raises(TursoError, match="hash"):
            pull(client, tmp_path / "restaurat")
    assert not any((tmp_path / "restaurat").iterdir())  # no queda res a mitges
