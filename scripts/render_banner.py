#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""Render the README banner — light and dark.

Usage:
    uv run scripts/render_banner.py [-o assets/]

Writes `banner-light.png` and `banner-dark.png` at 2× for retina; the README
shows them at half size behind a <picture> element so each theme gets its own.

Deliberately says nothing that can go stale. No version, no score, no claim
counts — a banner is not a reading, and a number frozen into an image is a
number nobody will remember to update. What it shows instead is the verdict
scale, which is the thing a first-time reader actually needs and the one part
of this tool that has not changed since 0.1.0.

Neo-brutalism: hard borders, offset shadows, no radius, no gradients. That
means rectangles and text, which is why this is Pillow and not a browser.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# 2×, displayed at 900 — GitHub's README column. Wider than this and the title
# floats in dead space on the right; the height is derived from the content
# below rather than guessed, so editing a line can't leave a band of empty card.
W = 1800
FONTS = Path(__file__).resolve().parent / "fonts"

MARGIN, SHADOW, PAD_X, PAD_TOP, PAD_BOTTOM = 40, 24, 76, 66, 72

YELLOW = "#FFF200"
VERDICTS = [
    ("CONFIRMED",    "#00FF00"),
    ("PLAUSIBLE",    "#FFFF00"),
    ("MISLEADING",   "#FF8800"),
    ("FALSE",        "#FF00FF"),
    ("UNVERIFIABLE", "#F5F5F5"),
]

THEMES = {
    "light": dict(page="#F5F5F5", card="#FFFFFF", ink="#000000", line="#000000"),
    # Not an inversion: the verdict chips keep their colours, because a reader
    # who has seen one BS artifact should recognise the next one whatever theme
    # they are in. Only the page, card and rules flip.
    "dark":  dict(page="#0A0A0A", card="#141414", ink="#FFFFFF", line="#FFFFFF"),
}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def text_w(d: ImageDraw.ImageDraw, s: str, f: ImageFont.FreeTypeFont) -> int:
    return int(d.textlength(s, font=f))


def fit(d, s: str, name: str, max_w: int, start: int, floor: int = 12):
    """Largest size at which `s` still fits `max_w`.

    Hardcoding a size means every edit to the copy — or to the canvas width — is
    a chance to silently clip a letter off the end. It already happened once.
    """
    size = start
    while size > floor and text_w(d, s, font(name, size)) > max_w:
        size -= 2
    return font(name, size)


def block(d, xy, wh, fill, line, width=6, shadow=0):
    """A bordered rectangle with an optional hard offset shadow."""
    x, y = xy
    w, h = wh
    if shadow:
        d.rectangle([x + shadow, y + shadow, x + w + shadow, y + h + shadow], fill=line)
    d.rectangle([x, y, x + w, y + h], fill=fill, outline=line, width=width)


def chip(d, x, y, label, colour, line, f, pad=(26, 16), shadow=8):
    w = text_w(d, label, f) + pad[0] * 2
    h = f.size + pad[1] * 2
    block(d, (x, y), (w, h), colour, line, width=6, shadow=shadow)
    # Chip colours are all light, so the label stays black in both themes.
    d.text((x + pad[0], y + pad[1] - 2), label, font=f, fill="#000000")
    return w


SUBTITLE = ("Point your agent at a video, article, tweet or PDF.",
            "Get every claim back — checked, scored, and sourced.")
RULE = "No source, no verdict — not even when the model is sure."

# (font size, gap that follows). Kept as data so the height below is derived
# from the same numbers the drawing uses.
EYEBROW_H, EYEBROW_GAP = 40 + 34, 42
TITLE_GAP, SUB_GAP, SUB_BLOCK_GAP, CHIP_GAP = 30, 14, 40, 48


def content_height(f_title, f_sub, f_chip, f_rule) -> int:
    return (EYEBROW_H + EYEBROW_GAP
            + f_title.size + TITLE_GAP
            + len(SUBTITLE) * (f_sub.size + SUB_GAP) + SUB_BLOCK_GAP
            + (f_chip.size + 32) + CHIP_GAP
            + f_rule.size + 14)


def render(theme: str) -> Image.Image:
    t = THEMES[theme]

    # Everything is measured against the usable width inside the card, so copy
    # and canvas can both change without anything running off the edge.
    avail = W - 2 * MARGIN - SHADOW - 2 * PAD_X
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    f_eyebrow = font("Inter-Black.ttf", 40)
    f_title = fit(probe, "BULLSHIT-DETECTOR", "Inter-Black.ttf", avail, 200)
    f_sub = fit(probe, max(SUBTITLE, key=len), "Inter-Bold.ttf", avail, 48)
    f_rule = fit(probe, RULE, "Inter-Bold.ttf", avail - 40, 44)

    # Chips are laid out in a row, so the constraint is their combined width.
    f_chip = font("Inter-Black.ttf", 36)
    while f_chip.size > 16 and sum(
            text_w(probe, lbl, f_chip) + 52 + 22 for lbl, _ in VERDICTS) > avail:
        f_chip = font("Inter-Black.ttf", f_chip.size - 2)

    inner = content_height(f_title, f_sub, f_chip, f_rule)
    card_h = PAD_TOP + inner + PAD_BOTTOM
    H = card_h + 2 * MARGIN + SHADOW

    img = Image.new("RGB", (W, H), t["page"])
    d = ImageDraw.Draw(img)

    m, shadow = MARGIN, SHADOW
    block(d, (m, m), (W - 2 * m - shadow, card_h), t["card"], t["line"],
          width=12, shadow=shadow)

    x = m + PAD_X
    y = m + PAD_TOP

    # Eyebrow — the one place the report-card look is quoted directly.
    ew = text_w(d, "BS REPORT", f_eyebrow) + 56
    d.rectangle([x, y, x + ew, y + EYEBROW_H], fill=t["ink"])
    d.text((x + 28, y + 14), "BS REPORT", font=f_eyebrow, fill=YELLOW)
    y += EYEBROW_H + EYEBROW_GAP

    d.text((x, y), "BULLSHIT-DETECTOR", font=f_title, fill=t["ink"])
    y += f_title.size + TITLE_GAP

    for ln in SUBTITLE:
        d.text((x, y), ln, font=f_sub, fill=t["ink"])
        y += f_sub.size + SUB_GAP
    y += SUB_BLOCK_GAP

    cx = x
    for label, colour in VERDICTS:
        cx += chip(d, cx, y, label, colour, t["line"], f_chip) + 22
    y += (f_chip.size + 32) + CHIP_GAP

    # The load-bearing rule, quoted the way a report quotes its bottom line.
    bar = 14
    d.rectangle([x, y, x + bar, y + f_rule.size + 14], fill=t["ink"])
    d.text((x + bar + 26, y), RULE, font=f_rule, fill=t["ink"])

    return img


def main() -> None:
    ap = argparse.ArgumentParser(description="Render the README banner")
    ap.add_argument("-o", "--outdir", default="assets")
    args = ap.parse_args()

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        p = out / f"banner-{theme}.png"
        render(theme).save(p, optimize=True)
        print(p)


if __name__ == "__main__":
    main()
