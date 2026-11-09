"""Core adaptive splitting algorithm.

All row-energy computations are numpy-vectorized (no per-pixel Python loops).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None  # long screenshots legitimately exceed the default guard

DEFAULT_MAX_HEIGHT = 4096
DEFAULT_OVERLAP = 24
DEFAULT_TOLERANCE = 400
DEFAULT_THRESHOLD = 0.02

SUPPORTED_FORMATS = {"png", "jpeg", "jpg", "webp"}


@dataclass
class Segment:
    index: int
    y_start: int
    y_end: int
    file: str
    cut_energy: Optional[float] = None  # energy of the row where this segment was cut (None = last segment)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "y_start": self.y_start,
            "y_end": self.y_end,
            "file": self.file,
            "cut_energy": self.cut_energy,
        }


@dataclass
class SplitResult:
    source: str
    width: int
    height: int
    segments: List[Segment] = field(default_factory=list)
    cuts: List[int] = field(default_factory=list)  # absolute y of each cut line
    params: dict = field(default_factory=dict)

    def manifest(self) -> dict:
        return {
            "source": self.source,
            "width": self.width,
            "height": self.height,
            "params": self.params,
            "cuts": self.cuts,
            "segments": [s.to_dict() for s in self.segments],
            "segment_count": len(self.segments),
        }


def load_image(path: str) -> Image.Image:
    """Load an image with EXIF orientation correction."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    return img


def row_energies(img: Image.Image) -> np.ndarray:
    """Per-row content energy in [0, ~1]: max(ink ratio, horizontal gradient energy).

    Vectorized over the whole image; background is the most common gray level.
    """
    gray = np.asarray(img.convert("L"))
    h, w = gray.shape
    if h == 0 or w == 0:
        return np.zeros(h, dtype=np.float64)
    g = gray.astype(np.int16)
    counts = np.bincount(gray.ravel(), minlength=256)
    bg = int(counts.argmax())
    ink = (np.abs(g - bg) > 24).sum(axis=1) / float(w)
    grad = np.abs(np.diff(g, axis=1)).sum(axis=1) / (255.0 * w)
    return np.maximum(ink, grad)


def _find_low_runs(mask: np.ndarray) -> List[tuple]:
    """Return [(start, end_exclusive), ...] of consecutive True runs."""
    runs = []
    start = None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(mask)))
    return runs


def find_cut_points(
    energies: np.ndarray,
    max_height: int = DEFAULT_MAX_HEIGHT,
    tolerance: int = DEFAULT_TOLERANCE,
    threshold: float = DEFAULT_THRESHOLD,
) -> List[int]:
    """Adaptive cut lines: lowest-energy safe rows near multiples of max_height.

    Hard constraint: a cut may only land on a row whose energy <= threshold
    (blank / separator rows). If the window has no safe row, the search extends
    downward until one is found (segment may exceed max-height rather than
    slicing through text).
    """
    n = len(energies)
    cuts: List[int] = []
    pos = 0
    while n - pos > max_height + tolerance:
        target = pos + max_height
        lo = pos + max_height - tolerance
        hi = min(target + tolerance, n - 1)
        cut = -1
        if hi > lo:
            window = energies[lo:hi]
            mask = window <= threshold
            runs = _find_low_runs(mask)
            if runs:
                # take the low-energy band whose center is closest to target
                def run_dist(r):
                    center = lo + (r[0] + r[1]) // 2
                    return abs(center - target), center

                _, best_center = min((run_dist(r) for r in runs), key=lambda t: t[0])
                cut = best_center
        if cut < 0:
            # extend downward: first safe row after the window (with room left for a tail)
            tail_min = 1
            idx = hi
            while idx < n - tail_min:
                if energies[idx] <= threshold:
                    cut = idx
                    break
                idx += 1
        if cut < 0:
            break  # no safe row at all: keep the remainder as one segment
        cuts.append(cut)
        pos = cut
    return cuts


def _cutline_preview(img: Image.Image, cuts: List[int], out_path: str) -> None:
    """Write a visualization image with red lines at cut positions."""
    from PIL import ImageDraw

    preview = img.convert("RGB").copy()
    draw = ImageDraw.Draw(preview)
    for y in cuts:
        draw.line([(0, y), (preview.width - 1, y)], fill=(255, 0, 0), width=3)
    preview.save(out_path)


def split_image(
    image_path: str,
    out_dir: Optional[str] = None,
    max_height: int = DEFAULT_MAX_HEIGHT,
    overlap: int = DEFAULT_OVERLAP,
    tolerance: int = DEFAULT_TOLERANCE,
    threshold: float = DEFAULT_THRESHOLD,
    out_format: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Split a long image adaptively. Returns the manifest dict.

    Writes segment files + manifest.json into out_dir (default: <stem>_parts
    next to the input). With dry_run=True only writes a cut-line preview.
    """
    image_path = os.path.abspath(image_path)
    img = load_image(image_path)
    w, h = img.size
    energies = row_energies(img)
    cuts = find_cut_points(energies, max_height, tolerance, threshold)

    stem = os.path.splitext(os.path.basename(image_path))[0]
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(image_path), stem + "_parts")
    os.makedirs(out_dir, exist_ok=True)

    fmt = (out_format or os.path.splitext(image_path)[1][1:] or "png").lower()
    fmt = {"jpg": "jpeg"}.get(fmt, fmt)
    if fmt not in {"png", "jpeg", "webp"}:
        fmt = "png"
    ext = {"jpeg": ".jpg"}.get(fmt, "." + fmt)

    result = SplitResult(
        source=image_path,
        width=w,
        height=h,
        cuts=cuts,
        params={
            "max_height": max_height,
            "overlap": overlap,
            "tolerance": tolerance,
            "threshold": threshold,
            "format": fmt,
        },
    )

    if dry_run:
        preview_path = os.path.join(out_dir, stem + "_cutlines.png")
        _cutline_preview(img, cuts, preview_path)
        result.params["dry_run"] = True
        result.params["preview"] = preview_path
        return result.manifest()

    # segment y-ranges: each segment extends `overlap` px beyond its internal cuts
    bounds = [0] + cuts + [h]
    for i in range(len(bounds) - 1):
        y_start = max(0, bounds[i] - (overlap if i > 0 else 0))
        y_end = min(h, bounds[i + 1] + (overlap if i < len(cuts) else 0))
        seg_img = img.crop((0, y_start, w, y_end))
        fname = f"{stem}_part{i + 1:02d}{ext}"
        seg_path = os.path.join(out_dir, fname)
        if fmt == "jpeg":
            seg_img = seg_img.convert("RGB")
        seg_img.save(seg_path)
        cut_energy = float(energies[cuts[i]]) if i < len(cuts) else None
        result.segments.append(Segment(i, y_start, y_end, seg_path, cut_energy))

    manifest_path = os.path.join(out_dir, "manifest.json")
    manifest = result.manifest()
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    manifest["manifest_path"] = manifest_path
    return manifest
