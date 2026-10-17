"""Fase 3: còpia a Turso per l'API HTTP (`/v2/pipeline`) i recuperació de l'arxiu (ADR 0005).

- `push`: puja les instantànies en cru que encara no hi són i reemplaça les taules
  derivades a partir de `data/viatges.sqlite`.
- `pull`: reconstrueix `data/raw/` a partir de l'arxiu de Turso, comprovant el hash.

Les transaccions de Turso han d'acabar en 5 segons. Per això les taules derivades es
carreguen primer en taules temporals (`_nou_*`) i després s'intercanvien en una sola
petició curta.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import math
import shutil
import sqlite3
import tempfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import httpx

from viatges.ingest import _write_json, list_snapshots

log = logging.getLogger(__name__)

DERIVED_TABLES = ["instantanies", "viatges", "trams", "canvis", "historial_ids"]
STATEMENTS_PER_REQUEST = 100
MAX_ARGS_PER_STATEMENT = 900  # per sota del límit clàssic de SQLite (999)

ARCHIVE_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS arxiu_instantanies (
        instantania TEXT PRIMARY KEY,
        manifest_json TEXT NOT NULL,
        metadata_json TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS arxiu_files (
        instantania TEXT NOT NULL,
        ordre INTEGER NOT NULL,
        id TEXT,
        fila_json TEXT NOT NULL,
        PRIMARY KEY (instantania, ordre)
    )""",
]

Statement = tuple[str, list[Any]]


class TursoError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Client HTTP
# ---------------------------------------------------------------------------


def encode_value(value: Any) -> dict[str, Any]:
    """Valor Python -> argument de l'API de Turso."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "integer", "value": str(int(value))}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    if isinstance(value, bytes):
        return {"type": "blob", "base64": base64.b64encode(value).decode()}
    return {"type": "text", "value": str(value)}


def decode_value(cell: dict[str, Any]) -> Any:
    kind = cell["type"]
    if kind == "null":
        return None
    if kind == "integer":
        return int(cell["value"])
    if kind == "float":
        return float(cell["value"])
    if kind == "blob":
        return base64.b64decode(cell["base64"])
    return cell["value"]


class TursoClient:
    def __init__(
        self,
        url: str,
        token: str,
        *,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        base_url = url.replace("libsql://", "https://", 1).replace("turso://", "https://", 1)
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            transport=transport,
        )

    def __enter__(self) -> TursoClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    def _pipeline(self, statements: list[Statement]) -> list[dict[str, Any]]:
        """Executa les sentències en una sola connexió i en retorna els resultats."""
        requests: list[dict[str, Any]] = [
            {
                "type": "execute",
                "stmt": {"sql": sql, "args": [encode_value(a) for a in args]},
            }
            for sql, args in statements
        ]
        requests.append({"type": "close"})
        response = self._client.post("/v2/pipeline", json={"requests": requests})
        response.raise_for_status()
        results = response.json()["results"]
        for (sql, _), result in zip(statements, results, strict=False):
            if result["type"] != "ok":
                message = result.get("error", {}).get("message", result)
                raise TursoError(f"{message} (sentència: {sql[:80]})")
        return [r["response"]["result"] for r in results[: len(statements)]]

    def execute(self, statements: Iterable[Statement]) -> None:
        """Executa moltes sentències, en peticions de `STATEMENTS_PER_REQUEST`."""
        batch: list[Statement] = []
        for statement in statements:
            batch.append(statement)
            if len(batch) == STATEMENTS_PER_REQUEST:
                self._pipeline(batch)
                batch = []
        if batch:
            self._pipeline(batch)

    def atomic(self, statements: list[Statement]) -> None:
        """Executa les sentències en una transacció, dins d'una sola petició."""
        self._pipeline([("BEGIN", []), *statements, ("COMMIT", [])])

    def query(self, sql: str, args: list[Any] | None = None) -> list[dict[str, Any]]:
        result = self._pipeline([(sql, args or [])])[0]
        names = [c["name"] for c in result["cols"]]
        return [dict(zip(names, map(decode_value, row), strict=True)) for row in result["rows"]]


# ---------------------------------------------------------------------------
# Construcció de sentències
# ---------------------------------------------------------------------------


def insert_statements(
    table: str, columns: list[str], rows: Iterable[tuple], verb: str = "INSERT"
) -> Iterator[Statement]:
    """INSERT de diverses files per sentència, sense passar de `MAX_ARGS_PER_STATEMENT`."""
    per_statement = max(1, MAX_ARGS_PER_STATEMENT // len(columns))
    cols = ", ".join(f'"{c}"' for c in columns)
    placeholder = "(" + ", ".join("?" * len(columns)) + ")"
    chunk: list[tuple] = []

    def flush() -> Statement:
        values = ", ".join([placeholder] * len(chunk))
        args = [value for row in chunk for value in row]
        return f'{verb} INTO "{table}" ({cols}) VALUES {values}', args

    for row in rows:
        chunk.append(row)
        if len(chunk) == per_statement:
            yield flush()
            chunk = []
    if chunk:
        yield flush()


# ---------------------------------------------------------------------------
# push i pull
# ---------------------------------------------------------------------------


def remote_snapshots(client: TursoClient) -> set[str]:
    client.execute((sql, []) for sql in ARCHIVE_SCHEMA)
    return {r["instantania"] for r in client.query("SELECT instantania FROM arxiu_instantanies")}


def push_snapshot(client: TursoClient, snapshot: Path) -> None:
    """Puja les files i, al final, la fila que marca la instantània com a completa."""
    rows = json.loads((snapshot / "rows.json").read_text(encoding="utf-8"))
    files = (
        (snapshot.name, i, row.get("id"), json.dumps(row, ensure_ascii=False))
        for i, row in enumerate(rows)
    )
    client.execute(
        insert_statements(
            "arxiu_files", ["instantania", "ordre", "id", "fila_json"], files, "INSERT OR REPLACE"
        )
    )
    manifest = (snapshot / "manifest.json").read_text(encoding="utf-8")
    metadata = (snapshot / "metadata.json").read_text(encoding="utf-8")
    client.execute(
        [
            (
                "INSERT OR REPLACE INTO arxiu_instantanies VALUES (?, ?, ?)",
                [snapshot.name, manifest, metadata],
            )
        ]
    )
    log.info("Instantània %s pujada a Turso (%d files)", snapshot.name, len(rows))


def push_derived_tables(client: TursoClient, db_path: Path) -> None:
    """Carrega les taules derivades a `_nou_*` i les intercanvia en una transacció curta."""
    with sqlite3.connect(db_path) as con:
        schema = dict(
            con.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'").fetchall()
        )
        indexes = con.execute(
            "SELECT tbl_name, sql FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL"
        ).fetchall()
        for table in DERIVED_TABLES:
            staging = f"_nou_{table}"
            create = schema[table].replace(
                f'CREATE TABLE "{table}"', f'CREATE TABLE "{staging}"', 1
            )
            cursor = con.execute(f'SELECT * FROM "{table}"')
            columns = [d[0] for d in cursor.description]
            client.execute([(f'DROP TABLE IF EXISTS "{staging}"', []), (create, [])])
            client.execute(insert_statements(staging, columns, cursor))
    swap: list[Statement] = []
    for table in DERIVED_TABLES:
        swap.append((f'DROP TABLE IF EXISTS "{table}"', []))
        swap.append((f'ALTER TABLE "_nou_{table}" RENAME TO "{table}"', []))
    swap.extend((sql, []) for table, sql in indexes if table in DERIVED_TABLES)
    client.atomic(swap)
    log.info("Taules derivades reemplaçades a Turso: %s", ", ".join(DERIVED_TABLES))


def push(client: TursoClient, raw_dir: Path, db_path: Path) -> None:
    remote = remote_snapshots(client)
    for snapshot in list_snapshots(raw_dir):
        if snapshot.name not in remote:
            push_snapshot(client, snapshot)
    push_derived_tables(client, db_path)


def pull(client: TursoClient, raw_dir: Path) -> list[Path]:
    """Descarrega les instantànies de l'arxiu que no són en local. Retorna les noves."""
    local = {p.name for p in list_snapshots(raw_dir)}
    new: list[Path] = []
    for name in sorted(remote_snapshots(client) - local):
        info = client.query(
            "SELECT manifest_json, metadata_json FROM arxiu_instantanies WHERE instantania = ?",
            [name],
        )[0]
        rows = client.query(
            "SELECT fila_json FROM arxiu_files WHERE instantania = ? ORDER BY ordre", [name]
        )
        manifest = json.loads(info["manifest_json"])
        raw_dir.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix=".tmp-", dir=raw_dir))
        try:
            raw = _write_json(tmp / "rows.json", [json.loads(r["fila_json"]) for r in rows])
            if hashlib.sha256(raw).hexdigest() != manifest.get("sha256_rows"):
                raise TursoError(f"El hash de {name} no coincideix amb el del manifest")
            (tmp / "metadata.json").write_text(info["metadata_json"], encoding="utf-8")
            (tmp / "manifest.json").write_text(info["manifest_json"], encoding="utf-8")
            tmp.rename(raw_dir / name)
        finally:
            if tmp.exists():
                shutil.rmtree(tmp)
        log.info("Instantània %s recuperada de Turso (%d files)", name, len(rows))
        new.append(raw_dir / name)
    return new
