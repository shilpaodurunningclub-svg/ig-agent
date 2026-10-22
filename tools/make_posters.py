"""
Builds the 20 stain-shade posters (JPEG, 1080x1350) from tools/shades.json.

Usage (from the project root):
    pip3 install playwright pillow
    python3 tools/make_posters.py

Edit tools/shades.json (names, colours, woods, articles, phone) and re-run to
regenerate every poster into posters/.
"""

import json
import re
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
OUT = ROOT / "posters"
TMP = ROOT / "tools" / "_html"
W, H = 1080, 1350

ICON_LABELS = {
    "table": "Dining table", "chair": "Chair", "wardrobe": "Wardrobe",
    "door": "Door", "bookshelf": "Bookshelf", "bench": "Bench",
}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(h):
    r, g, b = hex_to_rgb(h)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def icon_svg(kind, fill):
    detail = "rgba(0,0,0,0.30)" if luminance(fill) > 0.35 else "rgba(255,255,255,0.32)"
    stroke = "rgba(50,32,16,0.55)"
    shapes = {
        "table": f'''
            <rect x="8" y="28" width="104" height="12" rx="3"/>
            <rect x="20" y="40" width="80" height="7"/>
            <rect x="16" y="40" width="9" height="54"/><rect x="95" y="40" width="9" height="54"/>
            <rect x="8" y="38" width="104" height="2" fill="{detail}" stroke="none"/>''',
        "chair": f'''
            <rect x="34" y="6" width="9" height="50" rx="2"/><rect x="77" y="6" width="9" height="50" rx="2"/>
            <rect x="34" y="12" width="52" height="8" rx="2"/><rect x="34" y="28" width="52" height="8" rx="2"/>
            <rect x="28" y="52" width="64" height="11" rx="3"/>
            <rect x="32" y="63" width="8" height="32"/><rect x="80" y="63" width="8" height="32"/>
            <rect x="28" y="61" width="64" height="2" fill="{detail}" stroke="none"/>''',
        "wardrobe": f'''
            <rect x="18" y="2" width="84" height="7" rx="2"/>
            <rect x="22" y="9" width="76" height="80" rx="3"/>
            <rect x="28" y="89" width="9" height="8"/><rect x="83" y="89" width="9" height="8"/>
            <rect x="59" y="9" width="2" height="80" fill="{detail}" stroke="none"/>
            <circle cx="53" cy="50" r="2.8" fill="{detail}" stroke="none"/><circle cx="67" cy="50" r="2.8" fill="{detail}" stroke="none"/>''',
        "door": f'''
            <rect x="30" y="3" width="60" height="94" rx="3"/>
            <rect x="38" y="11" width="44" height="34" fill="none" stroke="{detail}" stroke-width="2.5"/>
            <rect x="38" y="53" width="44" height="36" fill="none" stroke="{detail}" stroke-width="2.5"/>
            <circle cx="81" cy="50" r="3.2" fill="{detail}" stroke="none"/>''',
        "bookshelf": f'''
            <rect x="22" y="4" width="76" height="92" rx="3"/>
            <rect x="27" y="33" width="66" height="3" fill="{detail}" stroke="none"/>
            <rect x="27" y="63" width="66" height="3" fill="{detail}" stroke="none"/>
            <rect x="32" y="12" width="6" height="21" fill="{detail}" stroke="none"/><rect x="41" y="16" width="6" height="17" fill="{detail}" stroke="none"/>
            <rect x="68" y="14" width="7" height="19" fill="{detail}" stroke="none"/>
            <rect x="34" y="42" width="7" height="21" fill="{detail}" stroke="none"/><rect x="74" y="46" width="12" height="17" fill="{detail}" stroke="none"/>''',
        "bench": f'''
            <rect x="8" y="42" width="104" height="13" rx="3"/>
            <rect x="16" y="55" width="9" height="38"/><rect x="95" y="55" width="9" height="38"/>
            <rect x="25" y="74" width="70" height="5"/>
            <rect x="8" y="53" width="104" height="2" fill="{detail}" stroke="none"/>''',
    }
    return (f'<svg viewBox="0 0 120 100" width="150" height="125" xmlns="http://www.w3.org/2000/svg" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.6" stroke-linejoin="round">{shapes[kind]}</svg>')


def swatch_background(color):
    light = luminance(color) > 0.45
    dark_line = "rgba(70,40,10,0.13)" if light else "rgba(255,255,255,0.06)"
    mid_line = "rgba(70,40,10,0.07)" if light else "rgba(255,255,255,0.035)"
    sheen = "rgba(255,255,255,0.18)" if light else "rgba(255,255,255,0.07)"
    return (
        f"linear-gradient(180deg, {sheen} 0%, rgba(255,255,255,0) 45%, rgba(0,0,0,0.10) 100%), "
        f"repeating-linear-gradient(0deg, {dark_line} 0px, {dark_line} 2px, rgba(0,0,0,0) 2px, rgba(0,0,0,0) 9px), "
        f"repeating-linear-gradient(0deg, {mid_line} 0px, {mid_line} 5px, rgba(0,0,0,0) 5px, rgba(0,0,0,0) 23px), "
        f"repeating-linear-gradient(0.4deg, {dark_line} 0px, {dark_line} 1px, rgba(0,0,0,0) 1px, rgba(0,0,0,0) 37px), "
        f"{color}"
    )


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def poster_html(cfg, shade, idx, total):
    chips = "".join(f'<span class="chip">{w}</span>' for w in shade["best"])
    items = "".join(
        f'<div class="item">{icon_svg(k, shade["color"])}<div class="lbl">{ICON_LABELS[k]}</div></div>'
        for k in shade["seen"]
    )
    fonts = f"""
    @font-face {{ font-family: 'PF'; font-weight: 700; src: url('file://{FONTS}/playfair-display-latin-700-normal.woff2') format('woff2'); }}
    @font-face {{ font-family: 'MR'; font-weight: 500; src: url('file://{FONTS}/manrope-latin-500-normal.woff2') format('woff2'); }}
    @font-face {{ font-family: 'MR'; font-weight: 600; src: url('file://{FONTS}/manrope-latin-600-normal.woff2') format('woff2'); }}
    @font-face {{ font-family: 'MR'; font-weight: 700; src: url('file://{FONTS}/manrope-latin-700-normal.woff2') format('woff2'); }}
    """
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{fonts}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; width: {W}px; height: {H}px; }}
body {{
  font-family: 'MR', sans-serif; color: #2b2118; position: relative; overflow: hidden;
  background: #ffffff;
}}
.frame {{ position: absolute; inset: 26px; border: 1.5px solid rgba(176,138,69,0.55); border-radius: 6px; pointer-events: none; }}
.page {{ position: absolute; inset: 0; padding: 66px 70px 58px; display: flex; flex-direction: column; }}
.top {{ display: flex; justify-content: space-between; align-items: center; font-size: 21px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #8a6a2f; }}
h1 {{ margin: 26px 0 0; font-family: 'PF', Georgia, serif; font-weight: 700; font-size: 106px; line-height: 1.04; color: #2b2118; }}
.look {{ margin: 14px 0 0; font-size: 29px; line-height: 1.38; font-weight: 500; color: #5a4a3b; max-width: 900px; }}
.swatch {{ margin-top: 30px; height: 290px; border-radius: 22px; background: {swatch_background(shade["color"])}; border: 2px solid rgba(90,70,45,0.28); box-shadow: 0 14px 30px rgba(60,40,15,0.18); }}
.row {{ margin-top: 30px; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }}
.tag {{ font-size: 19px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #8a6a2f; margin-right: 6px; }}
.chip {{ font-size: 25px; font-weight: 600; padding: 9px 22px; border-radius: 999px; border: 2px solid #B08A45; color: #2b2118; }}
.card {{ margin-top: 28px; background: #F3ECDF; border-radius: 22px; padding: 22px 30px 20px; color: #2a1a0d; }}
.card .tag {{ color: #6b4a2b; display: block; margin: 0 0 6px; }}
.items {{ display: flex; justify-content: space-around; align-items: flex-end; }}
.item {{ display: flex; flex-direction: column; align-items: center; gap: 6px; }}
.lbl {{ font-size: 22px; font-weight: 700; color: #2a1a0d; }}
.spacer {{ flex-grow: 1; }}
.features {{ text-align: center; font-size: 21px; font-weight: 600; letter-spacing: 0.04em; color: #6b5a48; white-space: pre; }}
.contact {{ margin-top: 18px; text-align: center; font-size: 28px; font-weight: 500; color: #2b2118; }}
.pill {{ margin: 12px auto 0; width: 520px; padding: 14px 0; border-radius: 999px; background: #D2AA62; color: #2a1a0d; text-align: center; font-size: 50px; font-weight: 700; letter-spacing: 0.01em; }}
.studio {{ margin-top: 16px; text-align: center; font-size: 22px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #8a6a2f; }}
</style></head><body>
<div class="frame"></div>
<div class="page" id="page">
  <div class="top"><span>Water-based wood stain</span><span>{idx:02d} / {total}</span></div>
  <h1>{shade["name"]}</h1>
  <div class="look">{shade["look"]}</div>
  <div class="swatch"></div>
  <div class="row"><span class="tag">Best on</span>{chips}</div>
  <div class="card"><span class="tag">Seen on</span><div class="items">{items}</div></div>
  <div class="spacer"></div>
  <div class="features">{cfg["features"]}</div>
  <div class="contact">{cfg["contact_line"]}</div>
  <div class="pill">{cfg["contact_phone"]}</div>
  <div class="studio">{cfg["studio"]}</div>
</div>
</body></html>"""


def main():
    cfg = json.loads((ROOT / "tools" / "shades.json").read_text())
    shades = cfg["shades"]
    OUT.mkdir(exist_ok=True)
    TMP.mkdir(exist_ok=True)
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for i, shade in enumerate(shades, 1):
            name = f"{i:02d}-{slug(shade['name'])}"
            html_path = TMP / f"{name}.html"
            html_path.write_text(poster_html(cfg, shade, i, len(shades)))
            page.goto(f"file://{html_path}")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(150)
            # layout check: the footer must stay inside the page and the spacer must not collapse
            fit = page.evaluate(
                """() => { const pg = document.getElementById('page');
                           const sp = document.querySelector('.spacer').getBoundingClientRect().height;
                           const last = document.querySelector('.studio').getBoundingClientRect().bottom;
                           return {spacer: sp, bottom: last, scroll: pg.scrollHeight}; }"""
            )
            if fit["spacer"] < 8 or fit["bottom"] > H - 40:
                problems.append((name, fit))
            png = TMP / f"{name}.png"
            page.screenshot(path=str(png))
            Image.open(png).convert("RGB").save(OUT / f"{name}.jpg", "JPEG", quality=93, optimize=True)
            print("made", OUT / f"{name}.jpg", fit)
        browser.close()
    if problems:
        print("LAYOUT PROBLEMS:", problems)
        sys.exit(1)


if __name__ == "__main__":
    main()
