"""PostgreSQL connections via psycopg2; credentials from AWS Secrets Manager only."""

from __future__ import annotations

import sys
from pathlib import Path

# Prefer this package's `config.py` over any top-level `config` on sys.path (e.g. repo root).
_ml_root = str(Path(__file__).resolve().parent)
try:
    sys.path.remove(_ml_root)
except ValueError:
    pass
sys.path.insert(0, _ml_root)

import json
from functools import lru_cache
from typing import Any, Dict

import boto3
import psycopg2
from psycopg2.extensions import connection as PGConnection

from config import (
    AWS_REGION,
    DEFAULT_DB_HOST,
    DEFAULT_DB_NAME,
    SECRETS_MANAGER_SECRET_ID,
)


@lru_cache(maxsize=1)
def get_db_credentials() -> Dict[str, Any]:
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=SECRETS_MANAGER_SECRET_ID)
    raw = resp["SecretString"]
    return json.loads(raw)


def _resolve_db_params() -> Dict[str, Any]:
    creds = get_db_credentials()
    host = creds.get("host") or creds.get("hostname") or DEFAULT_DB_HOST
    port = int(creds.get("port", 5432))
    user = creds.get("username") or creds.get("user")
    password = creds.get("password")
    dbname = (
        creds.get("dbname")
        or creds.get("database")
        or creds.get("db")
        or DEFAULT_DB_NAME
    )
    if not user or password is None:
        raise RuntimeError(
            "Secret must include username and password for RDS (from Secrets Manager)."
        )
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname,
    }


def get_connection() -> PGConnection:
    p = _resolve_db_params()
    return psycopg2.connect(
        host=p["host"],
        port=p["port"],
        user=p["user"],
        password=p["password"],
        dbname=p["dbname"],
        connect_timeout=30,
    )
