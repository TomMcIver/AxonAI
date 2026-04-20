"""S3 URI helpers for simulator data loaders.

Loaders in `ml/simulator/data/*_loader.py` accept either local filesystem
paths or `s3://bucket/key` URIs. The helper below normalises an input
path: for S3 URIs it downloads the object to a deterministic cache
directory and returns the local path; for everything else it returns the
input unchanged.

Rationale: calibration needs to be reproducible and cheap on re-run.
Caching in `data/raw/s3_cache/` means a second `fit_2pl` call on the
same dataset doesn't pay the S3 egress cost again. The cache key is
`bucket__key-with-slashes-replaced` so the mapping is one-to-one and
inspectable.

Env vars (standard boto3 chain):
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN (optional), AWS_DEFAULT_REGION.

No magic numbers; only a cache directory constant below.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

S3_PREFIX = "s3://"
DEFAULT_CACHE_DIR = Path("data/raw/s3_cache")


def is_s3_uri(path: str | Path) -> bool:
    return isinstance(path, str) and path.startswith(S3_PREFIX)


def parse_s3_uri(uri: str) -> tuple[str, str]:
    if not is_s3_uri(uri):
        raise ValueError(f"not an s3 uri: {uri!r}")
    without = uri[len(S3_PREFIX) :]
    bucket, _, key = without.partition("/")
    if not bucket or not key:
        raise ValueError(f"s3 uri must be s3://bucket/key, got {uri!r}")
    return bucket, key


def _cache_path(bucket: str, key: str, cache_dir: Path) -> Path:
    safe = key.replace("/", "__")
    return cache_dir / f"{bucket}__{safe}"


def materialise(
    path: str | Path,
    cache_dir: Optional[Path] = None,
) -> Path:
    """Return a local Path for `path`. Downloads from S3 if needed."""
    if not is_s3_uri(path):
        return Path(path)

    try:
        import boto3
    except ImportError as e:
        raise ImportError(
            "reading s3:// paths requires boto3; "
            "install via `pip install boto3` or the simulator extras."
        ) from e

    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    bucket, key = parse_s3_uri(str(path))
    local = _cache_path(bucket, key, cache_dir)
    if local.exists():
        return local

    s3 = boto3.client("s3")
    s3.download_file(bucket, key, str(local))
    return local


def materialise_prefix(
    prefix_uri: str,
    cache_dir: Optional[Path] = None,
) -> Path:
    """Materialise every object under an s3://bucket/prefix/ URI.

    Returns the local directory containing the downloaded objects.
    Directory layout mirrors the key suffixes below the prefix.
    """
    if not is_s3_uri(prefix_uri):
        return Path(prefix_uri)

    try:
        import boto3
    except ImportError as e:
        raise ImportError(
            "reading s3:// paths requires boto3; "
            "install via `pip install boto3` or the simulator extras."
        ) from e

    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    bucket, prefix = parse_s3_uri(prefix_uri)
    if not prefix.endswith("/"):
        prefix = prefix + "/"
    local_root = cache_dir / f"{bucket}__{prefix.rstrip('/').replace('/', '__')}"
    local_root.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            rel = key[len(prefix) :]
            dst = local_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                s3.download_file(bucket, key, str(dst))
    return local_root
