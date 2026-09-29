"""Punto de entrada: `uv run viatges <comando>`."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from viatges import config
from viatges.ingest import latest_snapshot, run_ingest
from viatges.profiling import run_profile


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="viatges", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="Descarga el dataset completo como instantánea cruda")
    profile = sub.add_parser("profile", help="Genera el inventario de calidad (Fase 0)")
    profile.add_argument(
        "--snapshot", type=Path, help="Carpeta de instantánea (por defecto, la última)"
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
        logging.info("Informe escrito en %s", out)


if __name__ == "__main__":
    main()
