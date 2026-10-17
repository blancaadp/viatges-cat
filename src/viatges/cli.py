"""Punt d'entrada: `uv run viatges <ordre>`."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from viatges import config
from viatges.clean import run_clean
from viatges.ingest import latest_snapshot, run_ingest
from viatges.profiling import run_profile


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="viatges", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="Descarrega el dataset complet com a instantània en cru")
    profile = sub.add_parser("profile", help="Genera l'inventari de qualitat (Fase 0)")
    profile.add_argument(
        "--snapshot", type=Path, help="Carpeta de la instantània (per defecte, la darrera)"
    )
    clean = sub.add_parser("clean", help="Neteja i normalitza una instantània (Fase 1)")
    clean.add_argument(
        "--snapshot", type=Path, help="Carpeta de la instantània (per defecte, la darrera)"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    if args.command == "ingest":
        run_ingest()
    elif args.command == "profile":
        snapshot = args.snapshot or latest_snapshot()
        out = run_profile(snapshot, config.REPORTS_DIR)
        logging.info("Informe escrit a %s", out)
    elif args.command == "clean":
        snapshot = args.snapshot or latest_snapshot()
        out = run_clean(snapshot, config.MANUAL_DIR, config.PROCESSED_DIR, config.REPORTS_DIR)
        logging.info("Dades netes a %s", out)


if __name__ == "__main__":
    main()
