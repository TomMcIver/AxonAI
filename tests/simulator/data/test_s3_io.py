"""Tests for ml.simulator.data.s3_io URI parsing helpers.

The network-backed download paths are exercised in PR A1's calibration
runs; these unit tests cover the pure-string logic.
"""

from __future__ import annotations

import pytest

from ml.simulator.data.s3_io import (
    is_s3_uri,
    materialise,
    parse_s3_uri,
)


def test_is_s3_uri_true():
    assert is_s3_uri("s3://bucket/key")
    assert is_s3_uri("s3://bucket/nested/key.csv")


def test_is_s3_uri_false():
    assert not is_s3_uri("/local/path.csv")
    assert not is_s3_uri("")
    assert not is_s3_uri("http://bucket/key")


def test_parse_s3_uri_splits_bucket_and_key():
    bucket, key = parse_s3_uri("s3://axon-datasets/assistments/file.csv")
    assert bucket == "axon-datasets"
    assert key == "assistments/file.csv"


def test_parse_s3_uri_rejects_non_s3():
    with pytest.raises(ValueError):
        parse_s3_uri("/local/path")


def test_parse_s3_uri_rejects_bucket_only():
    with pytest.raises(ValueError):
        parse_s3_uri("s3://bucket")


def test_materialise_returns_local_path_unchanged(tmp_path):
    local = tmp_path / "x.csv"
    local.write_text("a,b\n1,2\n")
    got = materialise(str(local))
    assert str(got) == str(local)
