"""Local parquet writer for simulator events.

Streams `TermRunner` events to `<output_dir>/<run_id>/*.parquet`, one
file per event type (`teach`, `attempt`, `revise`, `session_end`).
Events are buffered in per-type lists and flushed in batches so a full
term never sits in memory. `is_simulated=True` is stamped on every row
(non-negotiable).

A `manifest.json` lands alongside the parquet files, recording the
config hash, seed, row counts per file, and start/end wall-clock time.
The writer is a context manager:

    with LocalParquetWriter(output_dir, run_id, config) as w:
        for event in runner.run():
            w.write(event)

`close()` flushes residual buffers and writes the manifest.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from ml.simulator.config import SimulationConfig
from ml.simulator.loop.revise import ReviseRecord
from ml.simulator.loop.runner import SessionEndRecord
from ml.simulator.loop.teach import TeachRecord
from ml.simulator.student.profile import AttemptRecord

# Batch size before flushing a buffer to disk. 4096 keeps per-flush work
# cheap and parquet row-groups small enough to inspect with duckdb.
_BATCH_SIZE = 4096


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
    # `tuple[int, ...]` (ReviseRecord.concepts) is not a parquet type.
    for k, v in list(row.items()):
        if isinstance(v, tuple):
            row[k] = list(v)
    row["is_simulated"] = True
    return row


class LocalParquetWriter:
    def __init__(
        self,
        output_dir: str | Path,
        run_id: str,
        config: SimulationConfig,
    ) -> None:
        self.run_dir = Path(output_dir) / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.config = config
        self._buffers: dict[str, list[dict[str, Any]]] = {
            "teach": [],
            "attempt": [],
            "revise": [],
            "session_end": [],
        }
        self._writers: dict[str, pq.ParquetWriter] = {}
        self._row_counts: dict[str, int] = {k: 0 for k in self._buffers}
        self._started_at = datetime.now(timezone.utc)
        self._closed = False

    def __enter__(self) -> "LocalParquetWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def write(self, event: Any) -> None:
        kind = _event_kind(event)
        if kind is None:
            raise TypeError(f"Unknown event type: {type(event).__name__}")
        self._buffers[kind].append(_row_from_event(event))
        if len(self._buffers[kind]) >= _BATCH_SIZE:
            self._flush(kind)

    def write_many(self, events: Iterable[Any]) -> None:
        for e in events:
            self.write(e)

    def close(self) -> None:
        if self._closed:
            return
        for kind in list(self._buffers.keys()):
            if self._buffers[kind]:
                self._flush(kind)
        for writer in self._writers.values():
            writer.close()
        self._writers.clear()
        self._write_manifest()
        self._closed = True

    def _flush(self, kind: str) -> None:
        rows = self._buffers[kind]
        if not rows:
            return
        table = pa.Table.from_pylist(rows)
        if kind not in self._writers:
            path = self.run_dir / f"{kind}.parquet"
            self._writers[kind] = pq.ParquetWriter(path, table.schema)
        self._writers[kind].write_table(table)
        self._row_counts[kind] += len(rows)
        rows.clear()

    def _write_manifest(self) -> None:
        config_dict = asdict(self.config)
        # Normalise tuples for stable hashing.
        config_dict = {k: (list(v) if isinstance(v, tuple) else v) for k, v in config_dict.items()}
        config_bytes = json.dumps(config_dict, sort_keys=True).encode()
        config_hash = hashlib.sha256(config_bytes).hexdigest()
        manifest = {
            "run_id": self.run_id,
            "seed": self.config.seed,
            "config": config_dict,
            "config_sha256": config_hash,
            "row_counts": dict(self._row_counts),
            "started_at": self._started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "is_simulated": True,
        }
        with open(self.run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
