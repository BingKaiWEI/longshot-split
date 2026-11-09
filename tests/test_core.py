"""Core algorithm tests: safe cut lines, no text crossing, manifest contents."""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from synth import make_chat_image  # noqa: E402

from longshot_split.core import (  # noqa: E402
    find_cut_points,
    load_image,
    row_energies,
    split_image,
)


@pytest.fixture(scope="module")
def chat_png(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("src") / "chat.png")
    return make_chat_image(path, width=1000, height=8000)


def test_split_basic(chat_png, tmp_path):
    out = str(tmp_path / "out")
    manifest = split_image(chat_png, out_dir=out, max_height=4096)
    assert manifest["width"] == 1000 and manifest["height"] == 8000
    assert manifest["segment_count"] >= 2
    # coverage: segments (with overlap) tile the whole image
    assert manifest["segments"][0]["y_start"] == 0
    assert manifest["segments"][-1]["y_end"] == 8000
    for seg in manifest["segments"]:
        assert os.path.isfile(seg["file"])
        assert os.path.getsize(seg["file"]) > 0
    assert os.path.isfile(os.path.join(out, "manifest.json"))


def test_cuts_do_not_cross_text(chat_png, tmp_path):
    out = str(tmp_path / "out")
    manifest = split_image(chat_png, out_dir=out, max_height=4096)
    threshold = manifest["params"]["threshold"]
    img = load_image(chat_png)
    energies = row_energies(img)
    for cut in manifest["cuts"]:
        # hard constraint: every cut line is a safe row (below threshold)
        assert energies[cut] < threshold, f"cut {cut} energy {energies[cut]}"
        # direct pixel check: a +-3px band around the cut is pure background
        gray = np.asarray(img.convert("L"))
        band = gray[max(0, cut - 3) : cut + 4]
        assert (band == band.max()).all() or np.ptp(band) <= 2, f"text crossed at cut {cut}"


def test_segments_are_reasonable_height(chat_png, tmp_path):
    manifest = split_image(chat_png, out_dir=str(tmp_path / "o"), max_height=2000, overlap=24)
    for seg in manifest["segments"][:-1]:
        assert seg["y_end"] - seg["y_start"] <= 2000 + manifest["params"]["tolerance"] + 100


def test_overlap_present(chat_png, tmp_path):
    overlap = 40
    manifest = split_image(chat_png, out_dir=str(tmp_path / "o"), max_height=2000, overlap=overlap)
    segs = manifest["segments"]
    for a, b in zip(segs, segs[1:]):
        assert b["y_start"] < a["y_end"]  # adjacent segments overlap
        assert a["y_end"] - b["y_start"] >= overlap  # at least the requested overlap


def test_manifest_roundtrip(chat_png, tmp_path):
    out = str(tmp_path / "o")
    manifest = split_image(chat_png, out_dir=out, max_height=4096)
    with open(os.path.join(out, "manifest.json"), encoding="utf-8") as f:
        on_disk = json.load(f)
    assert on_disk["source"] == manifest["source"]
    assert on_disk["segment_count"] == manifest["segment_count"]
    assert all("cut_energy" in s for s in on_disk["segments"])


def test_dry_run(chat_png, tmp_path):
    out = str(tmp_path / "dry")
    manifest = split_image(chat_png, out_dir=out, max_height=4096, dry_run=True)
    assert manifest["params"]["dry_run"] is True
    assert os.path.isfile(manifest["params"]["preview"])
    # no segment files written
    assert not any(f.startswith("chat_part") for f in os.listdir(out))


def test_supports_jpeg_and_webp(tmp_path):
    img = Image.new("RGB", (400, 3000), "white")
    from PIL import ImageDraw

    d = ImageDraw.Draw(img)
    y = 20
    while y < 2900:
        d.text((20, y), "hello world test line", fill="black")
        y += 50
    jp = str(tmp_path / "t.jpg")
    wp = str(tmp_path / "t.webp")
    img.save(jp)
    img.save(wp)
    for p in (jp, wp):
        m = split_image(p, out_dir=str(tmp_path / ("o_" + os.path.basename(p))))
        assert m["segment_count"] >= 1


def test_exif_orientation(tmp_path):
    from PIL import ImageDraw, ImageOps

    img = Image.new("RGB", (300, 600), "white")
    ImageDraw.Draw(img).text((20, 20), "exif", fill="black")
    img = ImageOps.exif_transpose(img)
    p = str(tmp_path / "e.png")
    img.save(p, exif=img.getexif())
    m = split_image(p, out_dir=str(tmp_path / "o"))
    assert m["width"] == 300 and m["height"] == 600


def test_no_safe_row_extends_segment():
    # dense noise everywhere: algorithm must refuse to cut rather than slice text
    rng = np.random.default_rng(0)
    energies = rng.uniform(0.5, 1.0, size=10000)
    assert find_cut_points(energies, max_height=1000, tolerance=100) == []
