"""Command-line entry point for the simulator.

Usage:
    python -m ml.simulator run --config ml/simulator/configs/small.yaml
    python -m ml.simulator run --config configs/full.yaml --run-id my_run
    python -m ml.simulator migrate
    python -m ml.simulator validate --run-id <id>

Subcommands:
    run       — load a YAML config, generate students, stream events to
                the configured output target.
    migrate   — apply the simulator's Postgres migrations (idempotent).
    validate  — placeholder; filled in PR 10 (validation report).
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np

from ml.simulator.config import SimulationConfig
from ml.simulator.io.local_writer import LocalParquetWriter

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ml.simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a simulation from a YAML config.")
    run_p.add_argument("--config", required=True, help="Path to YAML config.")
    run_p.add_argument("--run-id", default=None, help="Run id (default: timestamp-uuid).")
    run_p.add_argument(
        "--output-dir",
        default=None,
        help="Override SimulationConfig.output_dir (local_parquet target).",
    )

    mig_p = sub.add_parser("migrate", help="Apply Postgres migrations.")
    mig_p.add_argument("--dsn", default=None, help="DSN override (else SIM_DATABASE_URL).")

    val_p = sub.add_parser("validate", help="Validation report (PR 10).")
    val_p.add_argument("--run-id", required=True)

    return parser


def _default_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def _cmd_run(args: argparse.Namespace) -> int:
    config = SimulationConfig.from_yaml(args.config)
    run_id = args.run_id or _default_run_id()
    output_dir = args.output_dir or config.output_dir

    if config.output_target != "local_parquet":
        # Postgres path requires fit artefacts + schema work exercised in PR 10.
        raise NotImplementedError(
            f"output_target={config.output_target!r} is stubbed; only "
            "local_parquet is wired for the smoke run."
        )

    # The runner proper needs a calibrated item bank + concept graph +
    # bkt params, none of which are present until the calibration step
    # runs end-to-end in PR 10. For PR 9 the CLI smoke test goes through
    # `_smoke_run` which fabricates a tiny in-memory setup purely to
    # exercise the wiring (config → runner → writer → parquet).
    from ml.simulator.cli_smoke import smoke_run  # lazy: avoids import on migrate.

    smoke_run(config=config, run_id=run_id, output_dir=output_dir)
    print(f"[simulator] wrote run {run_id} to {output_dir}/{run_id}")
    return 0


def _cmd_migrate(args: argparse.Namespace) -> int:
    try:
        import psycopg  # type: ignore
    except ImportError:
        print("psycopg not installed; install psycopg[binary] to run migrations.", file=sys.stderr)
        return 2

    import os
    dsn = args.dsn or os.environ.get("SIM_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        print("No DSN. Pass --dsn or export SIM_DATABASE_URL / DATABASE_URL.", file=sys.stderr)
        return 2

    scripts = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    if not scripts:
        print("No migrations to apply.")
        return 0

    with psycopg.connect(dsn) as conn:
        for script in scripts:
            sql = script.read_text()
            with conn.cursor() as cur:
                cur.execute(sql)
            print(f"[simulator] applied {script.name}")
        conn.commit()
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    print("validate is implemented in PR 10.", file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "migrate":
        return _cmd_migrate(args)
    if args.command == "validate":
        return _cmd_validate(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
