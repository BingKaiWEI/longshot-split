"""Shared test helper: synthesize a fake chat long screenshot."""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

TEXT = (
    "哈哈这个真的太搞笑了",
    "今天下午三点开会记得带上笔记本",
    "我这就把设计稿发给你看一下",
    "好的没问题收到收到",
    "明天早上九点准时出发别迟到",
    "这个需求今晚就得上线了吧",
    "辛苦辛苦回头请你吃饭",
    "刚才那个链接点不开再发一次",
)


def make_chat_image(path: str, width: int = 1000, height: int = 8000) -> str:
    """White background, dark text lines grouped in messages, blank gaps between."""
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    y = 40
    line_h = 30
    msg_gap = 70  # blank gap between messages — safe cut zone
    i = 0
    while y + line_h < height - 40:
        text = TEXT[i % len(TEXT)]
        i += 1
        draw.text((40, y), text, fill="black")
        y += line_h + msg_gap
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    img.save(path)
    return path
