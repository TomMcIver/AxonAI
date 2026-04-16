"""
Build DATABASE_SCHEMA.md live-catalog section from extract_rds_schema.py JSON.

Usage:
  python scripts/extract_rds_schema.py --output-json schema/axonai_snapshot.json
  python scripts/render_database_schema_md.py --json schema/axonai_snapshot.json --output DATABASE_SCHEMA.md

Or pipe: python scripts/extract_rds_schema.py | python scripts/render_database_schema_md.py --stdin --output DATABASE_SCHEMA.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone

# Distinct markers so prose never accidentally substring-matches the injector.
MARKER_BEGIN = "<!-- AXONAI_DB_LIVE_SCHEMA_START -->"
MARKER_END = "<!-- AXONAI_DB_LIVE_SCHEMA_END -->"


def fmt_val(v) -> str:
    if v is None:
        return ""
    s = str(v).replace("\n", " ")
    return s


def render_live_block(snapshot: dict) -> str:
    conn = snapshot.get("connection") or {}
    lines = [
        "## Live PostgreSQL catalog (pg_catalog)",
        "",
        f"- **Captured at (UTC)**: {snapshot.get('captured_at_utc', 'unknown')}",
        f"- **Host used**: `{conn.get('host', '')}`",
        f"- **Database**: `{conn.get('database', '')}`",
        "",
        "This section is generated from `scripts/extract_rds_schema.py` and replaces everything between the HTML markers in `DATABASE_SCHEMA.md`.",
        "",
    ]

    tables = snapshot.get("tables") or []
    if not tables:
        lines.append("*No tables returned (empty database or extraction error).*")
        return "\n".join(lines) + "\n"

    for t in sorted(tables, key=lambda x: (x.get("schema_name"), x.get("table_name"))):
        schema = t.get("schema_name")
        name = t.get("table_name")
        fq_label = f"{schema}.{name}" if schema and name else name
        lines.append(f"### `{fq_label}`")
        lines.append("")
        rc = t.get("row_count")
        lines.append(f"- **Row count**: `{rc}`")
        lines.append("")

        pk = t.get("primary_key") or []
        lines.append(f"- **Primary key**: {', '.join(f'`{c}`' for c in pk) if pk else '*(none)*'}")
        lines.append("")

        fks = t.get("foreign_keys") or []
        if fks:
            lines.append("- **Foreign keys**:")
            for fk in fks:
                lines.append(
                    f"  - `{fk.get('from_column')}` → "
                    f"`{fk.get('to_schema')}.{fk.get('to_table')}.{fk.get('to_column')}` "
                    f"(`{fk.get('constraint_name')}`)"
                )
            lines.append("")
        else:
            lines.append("- **Foreign keys**: *(none detected)*")
            lines.append("")

        lines.append("| Column | Data type | Nullable | Default |")
        lines.append("|--------|-----------|----------|---------|")
        for c in t.get("columns") or []:
            lines.append(
                "| `{col}` | {dt} | {nul} | {defv} |".format(
                    col=c.get("column_name"),
                    dt=fmt_val(c.get("data_type")),
                    nul="YES" if c.get("nullable") else "NO",
                    defv=fmt_val(c.get("default_value")) or "—",
                )
            )
        lines.append("")

        idxs = t.get("indexes") or []
        if idxs:
            lines.append("**Indexes**:")
            for i in idxs:
                lines.append(f"- `{i.get('indexname')}`: `{i.get('indexdef')}`")
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def inject(path: str, live_md: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            original = f.read()
    except FileNotFoundError:
        original = ""

    if MARKER_BEGIN in original and MARKER_END in original:
        pattern = re.compile(
            re.escape(MARKER_BEGIN) + r".*?" + re.escape(MARKER_END),
            re.DOTALL,
        )
        replacement = MARKER_BEGIN + "\n\n" + live_md.rstrip() + "\n\n" + MARKER_END
        new_content, n = pattern.subn(replacement, original, count=1)
        if n != 1:
            raise SystemExit("Could not replace exactly one live schema block (markers missing or duplicated).")
        return new_content

    # New file: minimal wrapper
    return (
        "# AxonAI PostgreSQL — database schema\n\n"
        f"{MARKER_BEGIN}\n\n{live_md.rstrip()}\n\n{MARKER_END}\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Path to snapshot JSON")
    ap.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    ap.add_argument("--output", "-o", required=True, help="DATABASE_SCHEMA.md path to write or patch")
    ap.add_argument("--full-only", action="store_true", help="Write only the live block (no marker merge)")
    args = ap.parse_args()

    if args.stdin:
        snapshot = json.load(sys.stdin)
    elif args.json:
        with open(args.json, encoding="utf-8") as f:
            snapshot = json.load(f)
    else:
        ap.error("Provide --json path or --stdin")

    if "captured_at_utc" not in snapshot:
        snapshot["captured_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    live = render_live_block(snapshot)
    if args.full_only:
        sys.stdout.write(live)
        return

    merged = inject(args.output, live)
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(merged)


if __name__ == "__main__":
    main()
