#!/usr/bin/env python3
"""Restamp a channel manifest source into a target channel file.

Used by .github/workflows/promote.yml for both promote and rollback: the
workflow resolves which JSON content counts as the "source" (either another
channel's current file, for promote; or a prior git revision of the target
channel's own file, for rollback) and this script only re-stamps the
channel/promoted_at/promoted_by fields on top of it.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime


class SourceHasNoVersionError(ValueError):
    pass


def restamp(source: dict, *, channel: str, actor: str, now: str) -> dict:
    if not source.get("docker") and not source.get("lxc"):
        raise SourceHasNoVersionError("Source channel has no published version yet — nothing to promote.")
    result = dict(source)
    result["channel"] = channel
    result["promoted_at"] = now
    result["promoted_by"] = actor
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", required=True, choices=["staging", "stable"])
    parser.add_argument("--source-file", required=True, type=argparse.FileType("r"))
    parser.add_argument("--actor", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    source = json.load(args.source_file)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        result = restamp(source, channel=args.channel, actor=args.actor, now=now)
    except SourceHasNoVersionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    print(f"Wrote {args.out}: version={result.get('version')}, channel={result['channel']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
