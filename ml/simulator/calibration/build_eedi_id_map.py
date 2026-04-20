"""Phase 2 PR B1 — build the Eedi misconception int-mapping artefact.

The Phase 2 concern list (§plan, concern 1) flags a key-type mismatch:
`StudentProfile.misconception_susceptibility` is `dict[int, float]`,
but Eedi's canonical label `Misconception_123` sounds string-shaped.
In fact the Kaggle release's `misconception_mapping.csv` already uses
integer `MisconceptionId` — so we commit a *passthrough* mapping that
records (a) the canonical catalogue order and (b) a contiguous
0..N-1 index, so downstream code that needs a dense array position
has one without re-sorting.

Output shape (`data/processed/eedi_misconception_id_map.json`):

    {
        "_meta": {
            "source_csv": "<path used>",
            "n_misconceptions": 2587,
            "id_min": 0,
            "id_max": 2612
        },
        "entries": [
            {"eedi_id": 0, "index": 0, "name": "Does not know..."},
            {"eedi_id": 1, "index": 1, "name": "..."},
            ...
        ]
    }

`eedi_id` is the original Kaggle MisconceptionId; `index` is the dense
position (identical to list index above, kept explicit for clarity).
`entries` is sorted ascending by `eedi_id`.

Idempotent: running twice on the same catalogue produces identical
output. No sampling involved.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.simulator.data.eedi_misconceptions_loader import load

DEFAULT_OUT_PATH = "data/processed/eedi_misconception_id_map.json"


def build(
    questions_path: str,
    mapping_path: str | None = None,
    out_path: str = DEFAULT_OUT_PATH,
) -> Path:
    frames = load(questions_path, mapping_path)
    cat = frames.misconception_catalogue_df.copy()
    cat = cat.dropna(subset=["MisconceptionId"]).sort_values("MisconceptionId")
    cat = cat.reset_index(drop=True)

    entries = []
    for idx, row in cat.iterrows():
        entries.append(
            {
                "eedi_id": int(row["MisconceptionId"]),
                "index": int(idx),
                "name": str(row.get("MisconceptionName", "") or ""),
            }
        )
    payload = {
        "_meta": {
            "source_csv": str(questions_path),
            "mapping_csv": str(mapping_path) if mapping_path else None,
            "n_misconceptions": len(entries),
            "id_min": int(entries[0]["eedi_id"]) if entries else None,
            "id_max": int(entries[-1]["eedi_id"]) if entries else None,
        },
        "entries": entries,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    return out


def load_id_map(path: str | Path = DEFAULT_OUT_PATH) -> list[int]:
    """Read back the eedi_id list in canonical catalogue order."""
    payload = json.loads(Path(path).read_text())
    return [int(e["eedi_id"]) for e in payload["entries"]]


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Eedi misconception ID map.")
    ap.add_argument(
        "--questions",
        required=True,
        help="Path or s3:// URI for the Eedi questions CSV (or a prefix "
        "pointing at the Kaggle folder).",
    )
    ap.add_argument(
        "--mapping",
        default=None,
        help="Optional path or s3:// URI for misconception_mapping.csv.",
    )
    ap.add_argument("--out", default=DEFAULT_OUT_PATH)
    args = ap.parse_args()
    out = build(args.questions, args.mapping, args.out)
    print(f"[B1] wrote id-map to {out}")


if __name__ == "__main__":
    main()
