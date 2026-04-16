"""
Introspect AxonAI PostgreSQL on RDS (tables, columns, PK/FK, indexes, row counts).

Requires: boto3, psycopg2-binary, AWS credentials (secretsmanager:GetSecretValue),
and network access to RDS (security group must allow your IP).

Examples:
  set AWS_REGION=ap-southeast-2
  set AXONAI_DB_HOST=axonai-db-prod.cl6susyag7hl.ap-southeast-2.rds.amazonaws.com
  set AXONAI_DB_NAME=axonai
  python scripts/extract_rds_schema.py --output-json schema/axonai_snapshot.json
  python scripts/render_database_schema_md.py --json schema/axonai_snapshot.json --output DATABASE_SCHEMA.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import boto3
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

DEFAULT_SECRET_ID = "axonai/db/credentials"
DEFAULT_REGION = "ap-southeast-2"


def get_secret(secret_id: str, region: str) -> dict:
    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=secret_id)
    return json.loads(resp["SecretString"])


def connect(secret: dict, host: str | None, dbname: str | None):
    h = host or secret.get("host")
    db = dbname or secret.get("dbname")
    if not h or not db:
        raise SystemExit("Host and database name are required (env or secret).")
    return psycopg2.connect(
        host=h,
        port=int(secret.get("port", 5432)),
        dbname=db,
        user=secret["username"],
        password=secret["password"],
        connect_timeout=30,
    )


def fetch_all(cur, query, params=None):
    cur.execute(query, params or ())
    return cur.fetchall()


def main():
    p = argparse.ArgumentParser(description="Dump PostgreSQL schema metadata to JSON.")
    p.add_argument("--secret-id", default=os.environ.get("AXONAI_DB_SECRET_ID", DEFAULT_SECRET_ID))
    p.add_argument("--region", default=os.environ.get("AWS_REGION", DEFAULT_REGION))
    p.add_argument(
        "--host",
        default=os.environ.get("AXONAI_DB_HOST"),
        help="RDS hostname (defaults to AXONAI_DB_HOST env or secret host)",
    )
    p.add_argument(
        "--database",
        default=os.environ.get("AXONAI_DB_NAME"),
        help="Database name (defaults to AXONAI_DB_NAME env or secret dbname)",
    )
    p.add_argument("--output-json", "-o", help="Write JSON snapshot to this path (stdout if omitted)")
    args = p.parse_args()

    secret = get_secret(args.secret_id, args.region)
    conn = connect(secret, args.host, args.database)
    conn.autocommit = True

    out = {
        "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "connection": {
            "host": args.host or secret.get("host"),
            "database": args.database or secret.get("dbname"),
            "region": args.region,
            "secret_id": args.secret_id,
        },
        "tables": [],
    }

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        tables = fetch_all(
            cur,
            """
            SELECT n.nspname AS schema_name, c.relname AS table_name
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'r'
              AND n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
              AND n.nspname NOT LIKE 'pg_%'
            ORDER BY n.nspname, c.relname
            """,
        )

        for row in tables:
            schema = row["schema_name"]
            table = row["table_name"]

            cols = fetch_all(
                cur,
                """
                SELECT
                    a.attname AS column_name,
                    format_type(a.atttypid, a.atttypmod) AS data_type,
                    (NOT a.attnotnull) AS nullable,
                    pg_get_expr(ad.adbin, ad.adrelid) AS default_value
                FROM pg_attribute a
                JOIN pg_class cl ON cl.oid = a.attrelid
                JOIN pg_namespace ns ON ns.oid = cl.relnamespace
                LEFT JOIN pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
                WHERE ns.nspname = %s AND cl.relname = %s
                  AND a.attnum > 0 AND NOT a.attisdropped
                ORDER BY a.attnum
                """,
                (schema, table),
            )

            pk_rows = fetch_all(
                cur,
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_schema = kcu.constraint_schema
                 AND tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = %s AND tc.table_name = %s
                  AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position
                """,
                (schema, table),
            )
            pk_cols = [r["column_name"] for r in pk_rows]

            fk_rows = fetch_all(
                cur,
                """
                SELECT
                    tc.constraint_name,
                    kcu.column_name AS from_column,
                    ccu.table_schema AS to_schema,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.table_schema = kcu.table_schema
                 AND tc.table_name = kcu.table_name
                 AND tc.constraint_name = kcu.constraint_name
                JOIN information_schema.referential_constraints rc
                  ON tc.constraint_schema = rc.constraint_schema
                 AND tc.constraint_name = rc.constraint_name
                JOIN information_schema.key_column_usage ccu
                  ON rc.unique_constraint_schema = ccu.constraint_schema
                 AND rc.unique_constraint_name = ccu.constraint_name
                 AND ccu.ordinal_position = kcu.ordinal_position
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = %s AND tc.table_name = %s
                ORDER BY tc.constraint_name, kcu.ordinal_position
                """,
                (schema, table),
            )

            idx_rows = fetch_all(
                cur,
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = %s AND tablename = %s
                ORDER BY indexname
                """,
                (schema, table),
            )

            count_sql = sql.SQL("SELECT COUNT(*) AS c FROM {}.{}").format(
                sql.Identifier(schema),
                sql.Identifier(table),
            )
            cur.execute(count_sql)
            row_count = cur.fetchone()["c"]

            out["tables"].append(
                {
                    "schema_name": schema,
                    "table_name": table,
                    "columns": [dict(c) for c in cols],
                    "primary_key": pk_cols,
                    "foreign_keys": [dict(f) for f in fk_rows],
                    "indexes": [dict(i) for i in idx_rows],
                    "row_count": row_count,
                }
            )

    conn.close()

    text = json.dumps(out, indent=2, default=str)
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
