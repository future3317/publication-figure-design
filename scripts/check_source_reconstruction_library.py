#!/usr/bin/env python3
"""Lightweight installed-library check for source reconstructions."""

from source_reconstruction_library import main


if __name__ == "__main__":
    raise SystemExit(main(["check", *(__import__("sys").argv[1:])]))
