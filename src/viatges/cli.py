"""Punt d'entrada: `uv run viatges <ordre>`."""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

from viatges import config
from viatges.changes import read_manifest, run_changes
from viatges.ingest import latest_snapshot, list_snapshots, run_ingest
from viatges.prepare import run_prepare
from viatges.profiling import run_profile
from viatges.store import build_database
from viatges.turso import TursoClient, pull, push

SNAPSHOT_HELP = "Carpeta de la instantània (per defecte, la darrera)"


def _last_two_snapshots() -> tuple[Path, Path] | None:
    snapshots = list_snapshots(config.RAW_DIR)
    return (snapshots[-2], snapshots[-1]) if len(snapshots) >= 2 else None


def _changes(old: Path | None = None, new: Path | None = None) -> None:
    if old is None or new is None:
        pair = _last_two_snapshots()
        if pair is None:
            logging.info("Cal tenir almenys dues instantànies per comparar")
            return
        old, new = old or pair[0], new or pair[1]
    out = run_changes(old, new, config.REPORTS_DIR)
    logging.info("Informe de canvis a %s", out)


def _discard_if_unchanged(snapshot: Path) -> bool:
    """Esborra la instantània si les files són idèntiques a l'anterior (ADR 0005)."""
    snapshots = list_snapshots(config.RAW_DIR)
    previous = [s for s in snapshots if s.name < snapshot.name]
    if not previous:
        return False
    same = read_manifest(previous[-1])["sha256_rows"] == read_manifest(snapshot)["sha256_rows"]
    if same:
        shutil.rmtree(snapshot)
        logging.info("Cap canvi des de %s: no es desa la nova instantània", previous[-1].name)
    return same


def _turso() -> TursoClient:
    return TursoClient(*config.turso_credentials())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="viatges", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="Descarrega el dataset complet com a instantània en cru")
    profile = sub.add_parser("profile", help="Genera l'inventari de qualitat (Fase 0)")
    profile.add_argument("--snapshot", type=Path, help=SNAPSHOT_HELP)
    prepare = sub.add_parser("prepare", help="Prepara una instantània per a l'anàlisi (Fase 1)")
    prepare.add_argument("--snapshot", type=Path, help=SNAPSHOT_HELP)
    changes = sub.add_parser("changes", help="Compara dues instantànies (Fase 2)")
    changes.add_argument(
        "--old", type=Path, help="Instantània anterior (per defecte, la penúltima)"
    )
    changes.add_argument("--new", type=Path, help="Instantània nova (per defecte, la darrera)")
    sub.add_parser("build", help="Reconstrueix la base de dades SQLite (Fase 2)")
    sub.add_parser("update", help="Ingesta + canvis + preparació + base de dades")
    sub.add_parser("push", help="Puja instantànies i taules a Turso (Fase 3)")
    sub.add_parser("pull", help="Recupera de Turso les instantànies que falten en local")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)  # una línia per petició és soroll

    if args.command == "ingest":
        run_ingest()
    elif args.command == "profile":
        snapshot = args.snapshot or latest_snapshot()
        out = run_profile(snapshot, config.REPORTS_DIR)
        logging.info("Informe escrit a %s", out)
    elif args.command == "prepare":
        snapshot = args.snapshot or latest_snapshot()
        out = run_prepare(snapshot, config.MANUAL_DIR, config.PROCESSED_DIR, config.REPORTS_DIR)
        logging.info("Dades preparades a %s", out)
    elif args.command == "changes":
        _changes(args.old, args.new)
    elif args.command == "build":
        build_database(config.RAW_DIR, config.MANUAL_DIR, config.DB_PATH)
    elif args.command == "update":
        snapshot = run_ingest()
        if not _discard_if_unchanged(snapshot):
            _changes()
        run_prepare(latest_snapshot(), config.MANUAL_DIR, config.PROCESSED_DIR, config.REPORTS_DIR)
        build_database(config.RAW_DIR, config.MANUAL_DIR, config.DB_PATH)
    elif args.command == "push":
        with _turso() as client:
            push(client, config.RAW_DIR, config.DB_PATH)
    elif args.command == "pull":
        with _turso() as client:
            new = pull(client, config.RAW_DIR)
        logging.info("Instantànies recuperades: %d", len(new))


if __name__ == "__main__":
    main()
