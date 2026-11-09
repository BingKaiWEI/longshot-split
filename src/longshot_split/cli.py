"""CLI for longshot-split."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core import (
    DEFAULT_MAX_HEIGHT,
    DEFAULT_OVERLAP,
    DEFAULT_THRESHOLD,
    DEFAULT_TOLERANCE,
    split_image,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="longshot-split",
        description="Adaptively split a long screenshot into segments, cutting only on safe blank rows.",
    )
    p.add_argument("image", help="input long image (PNG/JPEG/WebP)")
    p.add_argument("-o", "--out-dir", default=None, help="output directory (default: <name>_parts)")
    p.add_argument("--max-height", type=int, default=DEFAULT_MAX_HEIGHT, help="target segment height in px (default 4096)")
    p.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help="overlap between segments in px (default 24)")
    p.add_argument("--tolerance", type=int, default=DEFAULT_TOLERANCE, help="cut search window radius in px (default 400)")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="max row energy allowed at a cut line (default 0.02)")
    p.add_argument("--format", dest="out_format", default=None, choices=["png", "jpeg", "webp"], help="output format (default: same as input)")
    p.add_argument("--dry-run", action="store_true", help="only write a cut-line visualization image")
    p.add_argument("--version", action="version", version=f"longshot-split {__version__}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    manifest = split_image(
        args.image,
        out_dir=args.out_dir,
        max_height=args.max_height,
        overlap=args.overlap,
        tolerance=args.tolerance,
        threshold=args.threshold,
        out_format=args.out_format,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print(f"dry-run: {len(manifest['cuts'])} cut line(s) -> {manifest['params'].get('preview')}")
        print(json.dumps(manifest["cuts"]))
    else:
        print(f"split into {manifest['segment_count']} segment(s)")
        for seg in manifest["segments"]:
            print(f"  [{seg['y_start']:>6}, {seg['y_end']:>6}) {seg['file']}")
        print(f"manifest: {manifest['manifest_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
