from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _load_promote_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "promote.py"
    spec = importlib.util.spec_from_file_location("promote", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


promote = _load_promote_module()


FULL_SOURCE = {
    "channel": "canary",
    "version": "2026.7.0",
    "docker": {"image": "ghcr.io/abeggled/openbridgeserver", "digest": "sha256:abc123"},
    "lxc": {
        "version": "2026.7.0",
        "asset_url": "https://example.invalid/app-bundle.tar.gz",
        "sha256": "def456",
    },
    "promoted_at": "2026-07-01T00:00:00Z",
    "promoted_by": "release-ci",
}

EMPTY_SOURCE = {
    "channel": "staging",
    "version": None,
    "docker": None,
    "lxc": None,
    "promoted_at": None,
    "promoted_by": None,
}


def test_restamp_sets_channel_and_stamps():
    result = promote.restamp(FULL_SOURCE, channel="staging", actor="starwarsfan", now="2026-07-15T10:00:00Z")

    assert result["channel"] == "staging"
    assert result["promoted_at"] == "2026-07-15T10:00:00Z"
    assert result["promoted_by"] == "starwarsfan"


def test_restamp_preserves_docker_and_lxc_blocks():
    result = promote.restamp(FULL_SOURCE, channel="stable", actor="starwarsfan", now="2026-07-15T10:00:00Z")

    assert result["version"] == "2026.7.0"
    assert result["docker"] == FULL_SOURCE["docker"]
    assert result["lxc"] == FULL_SOURCE["lxc"]


def test_restamp_does_not_mutate_source():
    promote.restamp(FULL_SOURCE, channel="staging", actor="starwarsfan", now="2026-07-15T10:00:00Z")

    assert FULL_SOURCE["channel"] == "canary"
    assert FULL_SOURCE["promoted_by"] == "release-ci"


def test_restamp_rejects_source_without_docker_or_lxc():
    with pytest.raises(promote.SourceHasNoVersionError):
        promote.restamp(EMPTY_SOURCE, channel="stable", actor="starwarsfan", now="2026-07-15T10:00:00Z")


def test_cli_writes_restamped_manifest(tmp_path):
    source_file = tmp_path / "source.json"
    source_file.write_text(json.dumps(FULL_SOURCE), encoding="utf-8")
    out_file = tmp_path / "out.json"

    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "scripts" / "promote.py"),
            "--channel",
            "staging",
            "--source-file",
            str(source_file),
            "--actor",
            "starwarsfan",
            "--out",
            str(out_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    written = json.loads(out_file.read_text(encoding="utf-8"))
    assert written["channel"] == "staging"
    assert written["promoted_by"] == "starwarsfan"
    assert written["docker"] == FULL_SOURCE["docker"]


def test_cli_fails_clearly_on_empty_source(tmp_path):
    source_file = tmp_path / "source.json"
    source_file.write_text(json.dumps(EMPTY_SOURCE), encoding="utf-8")
    out_file = tmp_path / "out.json"

    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "scripts" / "promote.py"),
            "--channel",
            "stable",
            "--source-file",
            str(source_file),
            "--actor",
            "starwarsfan",
            "--out",
            str(out_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "no published version yet" in result.stderr
    assert not out_file.exists()
