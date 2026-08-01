#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "playwright",
#     "pillow",
# ]
# ///
"""Render a BS-report carousel from slides.json.

Usage:
    uv run render_carousel.py slides.json [-o outdir]

One-time setup (downloads headless Chromium):
    uv run --with playwright playwright install chromium

Output: slide-1.png ... slide-N.png (1080x1350) + carousel.pdf (for
LinkedIn document posts). If Chromium is missing, slides.html is still
written so the slides can be inspected in any browser.
"""

import argparse
import html
import json
import sys
from pathlib import Path

W, H = 1080, 1350

# Must stay in step with the verdict scale in SKILL.md, tally.py and
# report-card's render_report.py. `not checked` was missing here until 0.8.1
# and any carousel built from such a claim died with a KeyError.
VERDICTS = {
    "confirmed": ("#00FF00", "CONFIRMED"),
    "plausible": ("#FFFF00", "PLAUSIBLE"),
    "misleading": ("#FF8800", "MISLEADING"),
    "false": ("#FF00FF", "FALSE"),
    "unverifiable": ("#F5F5F5", "UNVERIFIABLE"),
    "not checked": ("#FFFFFF", "NOT CHECKED"),
}

CSS = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #666; font-family: 'Helvetica Neue', Arial, sans-serif; color: #000; }}
.slide {{
  width: {W}px; height: {H}px; background: #fff;
  border: 14px solid #000; padding: 80px 72px;
  display: flex; flex-direction: column; overflow: hidden;
  position: relative; margin: 24px auto;
}}
.kicker {{
  display: inline-block; align-self: flex-start;
  background: #000; color: #fff; font-weight: 900; font-size: 34px;
  letter-spacing: 4px; padding: 14px 28px; margin-bottom: 56px;
}}
.footer {{
  position: absolute; bottom: 44px; left: 72px; right: 72px;
  border-top: 8px solid #000; padding-top: 24px;
  font-weight: 700; font-size: 30px;
}}
.title {{ font-weight: 900; font-size: 66px; line-height: 1.15; margin-bottom: 36px; }}
.source {{ font-size: 34px; font-weight: 700; color: #000; margin-bottom: 56px; }}
.scorebox {{
  align-self: flex-start; background: #FFFF00; border: 10px solid #000;
  box-shadow: 20px 20px 0 #000; padding: 36px 56px;
}}
.scorebox .num {{ font-weight: 900; font-size: 150px; line-height: 1; }}
.scorebox .verdict {{ font-weight: 700; font-size: 38px; margin-top: 16px; }}
.chip {{
  display: inline-block; align-self: flex-start; border: 8px solid #000;
  font-weight: 900; font-size: 40px; letter-spacing: 3px;
  padding: 16px 30px; margin-bottom: 48px; box-shadow: 12px 12px 0 #000;
}}
.claim-n {{ font-weight: 900; font-size: 34px; letter-spacing: 4px; margin-bottom: 40px; }}
.claim {{
  font-weight: 900; font-size: 58px; line-height: 1.25;
  border-left: 14px solid #000; padding-left: 40px; margin-bottom: 56px;
}}
.evidence {{ font-size: 40px; line-height: 1.45; font-weight: 400; }}
.evidence b {{ font-weight: 900; }}
.cta-head {{ font-weight: 900; font-size: 76px; line-height: 1.15; margin-bottom: 64px; }}
.cta-line {{
  background: #F5F5F5; border: 8px solid #000; padding: 28px 32px;
  font-family: 'Courier New', monospace; font-weight: 700; font-size: 33px;
  margin-bottom: 32px; word-break: break-all;
}}
"""


def esc(s: str) -> str:
    return html.escape(str(s))


def require(d: dict, key: str, where: str):
    """Fetch a required field, or exit saying which one is missing.

    Everything here used to be direct dict access, so a slides.json with a
    typo'd key produced a traceback pointing at an f-string rather than a
    sentence naming the field. Slide *type* already failed this way; the rest
    did not.
    """
    if key not in d:
        sys.exit(f"ERROR: {where} is missing required field {key!r}")
    return d[key]


def verdict_style(value, where: str) -> tuple:
    """Colour and label for a verdict, or exit listing the valid ones.

    Deliberately not a neutral fallback chip. An unrecognised verdict is
    either a typo or a scale this renderer hasn't been taught, and guessing a
    colour would put a wrong verdict on a slide people share — the one failure
    a fact-checking tool cannot ship. Better to stop and say so.
    """
    key = str(value).strip().lower()
    if key not in VERDICTS:
        sys.exit(
            f"ERROR: {where} has unknown verdict {value!r}.\n"
            f"       Valid verdicts: {', '.join(VERDICTS)}"
        )
    return VERDICTS[key]


def hook_slide(meta: dict) -> str:
    where = "the hook slide"
    return f"""
  <div class="slide">
    <div class="kicker">BS REPORT</div>
    <div class="title">&ldquo;{esc(require(meta, 'title', where))}&rdquo;</div>
    <div class="source">{esc(require(meta, 'source', where))}</div>
    <div class="scorebox">
      <div class="num">{esc(require(meta, 'score', where))}/10</div>
      <div class="verdict">{esc(require(meta, 'verdict_line', where))}</div>
    </div>
    <div class="footer">{esc(require(meta, 'footer', where))}</div>
  </div>"""


def claim_slide(s: dict, meta: dict) -> str:
    where = f"claim slide {s.get('n') or '(unnumbered)'}"
    color, label = verdict_style(require(s, "verdict", where), where)
    return f"""
  <div class="slide">
    <div class="claim-n">CLAIM {esc(s.get('n', ''))}</div>
    <div class="claim">&ldquo;{esc(require(s, 'claim', where))}&rdquo;</div>
    <div class="chip" style="background:{color}">{label}</div>
    <div class="evidence">{esc(require(s, 'evidence', where))}</div>
    <div class="footer">{esc(require(meta, 'footer', where))}</div>
  </div>"""


def cta_slide(s: dict, meta: dict) -> str:
    lines = "".join(f'<div class="cta-line">{esc(l)}</div>' for l in s.get("lines", []))
    return f"""
  <div class="slide">
    <div class="kicker">TRY IT</div>
    <div class="cta-head">{esc(s.get('headline', 'Run it on anything'))}</div>
    {lines}
    <div class="footer">{esc(require(meta, 'footer', 'the CTA slide'))}</div>
  </div>"""


def build_html(spec: dict) -> str:
    parts = []
    for s in spec["slides"]:
        kind = s.get("type")
        if kind == "hook":
            parts.append(hook_slide(spec))
        elif kind == "claim":
            parts.append(claim_slide(s, spec))
        elif kind == "cta":
            parts.append(cta_slide(s, spec))
        else:
            sys.exit(f"ERROR: unknown slide type {kind!r}")
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(parts)}</body></html>"


def main() -> None:
    ap = argparse.ArgumentParser(description="Render BS-report carousel slides")
    ap.add_argument("spec", help="path to slides.json")
    ap.add_argument("-o", "--outdir", default="carousel", help="output directory")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    html_path = outdir / "slides.html"
    html_path.write_text(build_html(spec), encoding="utf-8")
    print(f"wrote {html_path}")

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": W + 100, "height": H + 100})
            page.goto(html_path.resolve().as_uri())
            pngs = []
            for i, el in enumerate(page.locator(".slide").all(), 1):
                png = outdir / f"slide-{i}.png"
                el.screenshot(path=str(png))
                pngs.append(png)
                print(f"wrote {png}")
            browser.close()
    except Exception as e:
        print(f"\nERROR: could not render PNGs ({e})", file=sys.stderr)
        print("HINT: run `uv run --with playwright playwright install chromium` once, then retry.", file=sys.stderr)
        print(f"HINT: {html_path} is viewable in any browser meanwhile.", file=sys.stderr)
        sys.exit(2)

    # LinkedIn "carousel" = a PDF document post
    from PIL import Image

    images = [Image.open(p).convert("RGB") for p in pngs]
    pdf_path = outdir / "carousel.pdf"
    images[0].save(pdf_path, save_all=True, append_images=images[1:], resolution=96)
    print(f"wrote {pdf_path}")


if __name__ == "__main__":
    main()
