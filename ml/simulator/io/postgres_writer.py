"""Postgres writer — streams events into sim_* shadow tables.

Writes to a **separate** table set (`sim_attempts`, `sim_sessions`,
`sim_teach`, `sim_revise`) mirroring the real schema 1:1 but isolated
from production analytics. Every row is tagged `is_simulated=True`
(non-negotiable, even in shadow tables — downstream joins should never
confuse simulated rows for real ones).

Connection URL is read from `SIM_DATABASE_URL` with a fallback to
`DATABASE_URL`, so a run can target a staging instance without touching
prod by exporting `SIM_DATABASE_URL` once.

Schema creation lives in `ml/simulator/migrations/0001_is_simulated.sql`
and is applied via `python -m ml.simulator migrate`.

This module is intentionally small: batched INSERTs via psycopg (v3) if
installed, otherwise it raises on construction so local_parquet remains
the frictionless default.
"""

from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from typing import Any

from ml.simulator.loop.revise import ReviseRecord
from ml.simulator.loop.runner import SessionEndRecord
from ml.simulator.loop.teach import TeachRecord
from ml.simulator.student.profile import AttemptRecord

_BATCH_SIZE = 1024

_TABLE_BY_KIND = {
    "teach": "sim_teach",
    "attempt": "sim_attempts",
    "revise": "sim_revise",
    "session_end": "sim_sessions",
}


def _event_kind(event: Any) -> str | None:
    if isinstance(event, TeachRecord):
        return "teach"
    if isinstance(event, AttemptRecord):
        return "attempt"
    if isinstance(event, ReviseRecord):
        return "revise"
    if isinstance(event, SessionEndRecord):
        return "session_end"
    return None


def _row_from_event(event: Any) -> dict[str, Any]:
    row = asdict(event) if is_dataclass(event) else dict(event.__dict__)
    for k, v in list(row.items()):
        if isinstance(v, tuple):
            row[k] = list(v)
    row["is_simulated"] = True
    return row


def _resolve_dsn(explicit: str | None) -> str:
    if explicit:
        return explicit
    dsn = os.environ.get("SIM_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "Postgres writer needs SIM_DATABASE_URL or DATABASE_URL set "
            "(or pass dsn= explicitly)."
        )
    return dsn


class PostgresWriter:
    def __init__(self, run_id: str, dsn: str | None = None) -> None:
        try:
            import psycopg  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "psycopg is required for PostgresWriter; install psycopg[binary] "
                "or use output_target=local_parquet."
            ) from e
        self._psycopg = psycopg
        self.run_id = run_id
        self.dsn = _resolve_dsn(dsn)
        self._conn = psycopg.connect(self.dsn)
        self._buffers: dict[str, list[dict[str, Any]]] = {k: [] for k in _TABLE_BY_KIND}
        self._row_counts: dict[str, int] = {k: 0 for k in _TABLE_BY_KIND}
        self._closed = False

    def __enter__(self) -> "PostgresWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def write(self, event: Any) -> None:
        kind = _event_kind(event)
        if kind is None:
            raise TypeError(f"Unknown event type: {type(event).__name__}")
        row = _row_from_event(event)
        row["run_id"] = self.run_id
        self._buffers[kind].append(row)
        if len(self._buffers[kind]) >= _BATCH_SIZE:
            self._flush(kind)

    def close(self) -> None:
        if self._closed:
            return
        for kind in list(self._buffers.keys()):
            if self._buffers[kind]:
                self._flush(kind)
        self._conn.commit()
        self._conn.close()
        self._closed = True

    def _flush(self, kind: str) -> None:
        rows = self._buffers[kind]
        if not rows:
            return
        table = _TABLE_BY_KIND[kind]
        columns = list(rows[0].keys())
        col_sql = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"
        values = [[r[c] for c in columns] for r in rows]
        with self._conn.cursor() as cur:
            cur.executemany(sql, values)
        self._row_counts[kind] += len(rows)
        rows.clear()
