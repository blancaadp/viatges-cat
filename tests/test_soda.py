import httpx
import pytest

from viatges.soda import SodaClient


def test_fetch_all_pagina_hasta_pagina_incompleta():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["$offset"])
        calls.append(offset)
        remaining = max(0, 5 - offset)
        return httpx.Response(200, json=[{"n": offset + i} for i in range(min(2, remaining))])

    with SodaClient("example.org", transport=httpx.MockTransport(handler)) as client:
        rows = client.fetch_all("abcd-1234", page_size=2)

    assert [r["n"] for r in rows] == [0, 1, 2, 3, 4]
    assert calls == [0, 2, 4]


def test_reintenta_errores_temporales():
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with SodaClient("example.org", transport=transport, backoff_base=0) as client:
        assert client.metadata("abcd-1234") == {"ok": True}
    assert attempts["n"] == 3


def test_no_reintenta_errores_del_cliente():
    transport = httpx.MockTransport(lambda r: httpx.Response(404))
    with (
        SodaClient("example.org", transport=transport, backoff_base=0) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        client.metadata("abcd-1234")


def test_envia_app_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["token"] = request.headers.get("X-App-Token")
        return httpx.Response(200, json={})

    with SodaClient("example.org", "secreto", transport=httpx.MockTransport(handler)) as c:
        c.metadata("abcd-1234")
    assert seen["token"] == "secreto"
