#!/usr/bin/env python3
"""Audit actual PDF ``Tf`` text sizes in plain or FlateDecode streams.

Adapted from Yuan1z0825/nature-skills (Apache-2.0), nature-figure PDF text audit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zlib
from pathlib import Path


STREAM_START = re.compile(rb"stream\r?\n")
TF_OPERATOR = re.compile(
    rb"/([^\s/<>]+)\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)\s+Tf\b"
)


def decoded_streams(data: bytes) -> tuple[list[bytes], list[str]]:
    streams: list[bytes] = []
    warnings: list[str] = []
    cursor = 0
    number = 0
    while match := STREAM_START.search(data, cursor):
        number += 1
        end = data.find(b"endstream", match.end())
        if end < 0:
            warnings.append(f"stream {number} has no endstream marker")
            break
        payload = data[match.end():end]
        header = data[max(0, match.start() - 2048):match.start()]
        dictionary_start = header.rfind(b"<<")
        dictionary = header[dictionary_start:] if dictionary_start >= 0 else header
        if b"/FlateDecode" in dictionary:
            try:
                payload = zlib.decompress(payload)
            except zlib.error as exc:
                warnings.append(f"stream {number} FlateDecode failed: {exc}")
                cursor = end + len(b"endstream")
                continue
        elif b"/Filter" in dictionary:
            warnings.append(f"stream {number} uses an unsupported PDF filter")
            cursor = end + len(b"endstream")
            continue
        streams.append(payload)
        cursor = end + len(b"endstream")
    return streams, warnings


def audit_pdf(data: bytes, minimum_pt: float = 5.0) -> dict[str, object]:
    streams, warnings = decoded_streams(data)
    runs: list[dict[str, object]] = []
    for stream_number, stream in enumerate(streams, 1):
        for match in TF_OPERATOR.finditer(stream):
            size = float(match.group(2))
            if size > 0:
                runs.append({
                    "stream": stream_number,
                    "font": match.group(1).decode("ascii", errors="replace"),
                    "size_pt": size,
                })
    below = [run for run in runs if run["size_pt"] < minimum_pt]
    return {
        "auditable": bool(runs),
        "minimum_required_pt": minimum_pt,
        "minimum_found_pt": min((run["size_pt"] for run in runs), default=None),
        "text_run_count": len(runs),
        "below_minimum_count": len(below),
        "below_minimum": below,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--min-pt", type=float, default=5.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.min_pt <= 0:
        parser.error("--min-pt must be positive")
    try:
        data = args.pdf.read_bytes()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not data.startswith(b"%PDF-"):
        print(f"error: not a PDF file: {args.pdf}", file=sys.stderr)
        return 2
    report = audit_pdf(data, args.min_pt)
    if args.json:
        print(json.dumps({"pdf": str(args.pdf), **report}, indent=2, ensure_ascii=False))
    else:
        verdict = "NOT AUDITABLE" if not report["auditable"] else (
            "FAIL" if report["below_minimum_count"] else "PASS"
        )
        print(f"PDF text audit: {verdict}")
        print(f"minimum required: {args.min_pt:g} pt")
        print(f"minimum found: {report['minimum_found_pt']}")
        print(f"below minimum: {report['below_minimum_count']}")
    if not report["auditable"]:
        return 2
    return 1 if report["below_minimum_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
