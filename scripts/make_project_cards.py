"""Build assets/project-*.svg and thesis-banner*.svg: terminal windows for each project, matching profile.svg.

Run:  python scripts/make_project_cards.py   (needs Pillow and network access, for the thesis screenshot)
"""
import xml.dom.minidom
from pathlib import Path
from xml.sax.saxutils import escape

import make_card
from make_card import BAR, BG, BLUE, BORDER, BOX, CHAR_W, FONT, GREEN, GREY, PALETTES, ROOT, SUFFIX, WHITE, YELLOW, typing

W, H = 440, 290
_PREVIEW = "https://raw.githubusercontent.com/baselnasser99/Data-Tagging-Application/HEAD/docs/preview/"
# (screenshot, logo ink): the ink is the app's --ink token for that theme, from docs/preview/preview.html
THESIS_PREVIEW = {"dark": (_PREVIEW + "preview@2x-dark.png", "#E6EAF0"), "light": (_PREVIEW + "preview@2x.png", "#1C2733")}
PREVIEW_CSS_W = 1280  # the preview page's width in CSS pixels; its logo is 28 of them
PROJECTS = [
    {
        "slug": "data-tagging",
        "name": "Data-Tagging-Application",
        "facts": [
            ("What", "fair split of labelling work"),
            ("Rebalance", "live, as people come and go"),
            ("Export", "csv, json + agreement scores"),
            ("Stack", "flask, mysql, docker"),
            ("Tests", "300+ passing, ~94% coverage"),
        ],
        "status": ("shipped", GREEN),
        "typed": "open open-tasks --per-person",
        # open tasks per person after one leaves and one joins (from the project's preview)
        "bars": [8, 7, 8, 7, 8, 0, 7],
    },
    {
        "slug": "second-order",
        "name": "second-order",
        "facts": [
            ("Question", "why don't customers buy twice?"),
            ("Data", "olist marketplace, 9 tables"),
            ("Stack", "bigquery, dbt, sql, python"),
            ("Output", "where money is lost, fix first"),
        ],
        "status": ("in progress", YELLOW),
        "typed": "dbt run --select retention",
        "bars": None,
        "flow": ["9 csv files", "bigquery", "dbt", "insight"],
    },
]


def title_bar(name, w=W):
    tab_w = min(len(name) * 7 + 70, w - 160)
    right = w - 34 * 3
    return (f'<path d="M8 0h{w - 16}a8 8 0 0 1 8 8v26H0V8a8 8 0 0 1 8-8z" fill="{BAR}"/>'
            f'<path d="M8 34V14a6 6 0 0 1 6-6h{tab_w}a6 6 0 0 1 6 6v20z" fill="{BG}"/>'
            f'<text x="22" y="26" font-size="12" fill="{GREEN}" font-weight="700">&gt;_</text>'
            f'<text x="44" y="26" font-size="12" fill="{WHITE}">{escape(name)}</text>'
            f'<path d="M{right + 11} 21h12" stroke="{WHITE}" stroke-width="1"/>'
            f'<rect x="{right + 34 + 11.5}" y="15.5" width="11" height="11" fill="none" stroke="{WHITE}" stroke-width="1"/>'
            f'<path d="M{right + 68 + 11} 15l11 11m0-11l-11 11" stroke="{WHITE}" stroke-width="1"/>')


def moved_tasks(img):
    """Find the yellow 'moved to them' squares in the screenshot's chart, as (x, y, size, row) in image pixels."""
    import numpy as np

    a = np.asarray(img).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mask = (r > 200) & (g > 150) & (b < 110) & (r - b > 120)
    mask[:, :img.width // 2] = False  # the chart is on the right; the left has the yellow "fairly" highlight
    cells = []
    ys = np.where(mask.any(1))[0]
    for row, band in enumerate(np.split(ys, np.where(np.diff(ys) > 1)[0] + 1)):
        xs = np.where(mask[band[0]:band[-1] + 1].any(0))[0]
        for seg in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1):
            if seg[-1] - seg[0] >= img.width / 120:  # task squares only: skips the "just joined" label and the legend
                cells.append((seg[0], band[0], band[-1] - band[0] + 1, row))
    return cells


def live_logo(img, k, ink):
    """Cover the screenshot's logo and redraw it on top, moving like the app's own top-bar logo (app.css):
    the brackets close in on the yellow square and let go, like an item being tagged."""
    import numpy as np

    a = np.asarray(img).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mask = (r > 200) & (g > 150) & (b < 110) & (r - b > 120)
    mask[int(img.height * 0.3):, :] = False
    mask[:, int(img.width * 0.15):] = False  # the logo sits top left
    ys, xs = np.where(mask)
    cx, cy = xs.mean() + 0.5, ys.mean() + 0.5  # centre of the yellow square, which is the logo's centre
    u = img.width / PREVIEW_CSS_W  # image pixels per logo unit (the logo is 28 units)
    bg = "#%02x%02x%02x" % tuple(a[int(cy - 20 * u), int(cx - 20 * u)])
    x, y, size = (cx - 14 * u) * k, 34 + (cy - 14 * u) * k, 28 * u * k
    return (f'<rect x="{x - 1:.1f}" y="{y - 1:.1f}" width="{size + 2:.1f}" height="{size + 2:.1f}" fill="{bg}"/>'
            f'<g transform="translate({x:.2f} {y:.2f}) scale({u * k:.4f})">'
            f'<path class="select" d="M2 9V2h7M19 2h7v7M26 19v7h-7M9 26H2v-7" fill="none" stroke="{ink}" stroke-width="2.5" stroke-linecap="square"/>'
            f'<rect class="tag" x="10" y="10" width="8" height="8" rx="1" fill="#F5CF3A"/></g>')


def banner(name, url, ink, w=900, px=1800):
    """The thesis screenshot inside a terminal window. GitHub blocks images that an SVG loads from elsewhere,
    so the screenshot is downloaded and embedded; rerun this when the thesis preview changes."""
    import base64, io, urllib.request
    from PIL import Image

    img = Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=30).read())).convert("RGB")
    img = img.resize((px, round(px * img.height / img.width)), Image.LANCZOS)  # 2x the shown width stays sharp
    buf = io.BytesIO()
    img.quantize(256, dither=Image.Dither.NONE).save(buf, "PNG", optimize=True)  # flat UI colours: a third of the size
    data = base64.b64encode(buf.getvalue()).decode()
    h = 34 + round(w * img.height / img.width)
    k = w / img.width
    # the moved tasks glow one row after another, as if they were being handed out again
    glow = "".join(f'<rect class="glow" style="animation-delay:{row * 0.18:.2f}s" x="{x * k:.1f}" y="{34 + y * k:.1f}" '
                   f'width="{s * k:.1f}" height="{s * k:.1f}" rx="{1.5 * s * k / 10:.1f}"/>' for x, y, s, row in moved_tasks(img))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(name)}: labelling work, shared fairly. Open tasks per person stay within one task of each other after one person leaves and another joins.">
<style>
text {{ font-family: {FONT}; }}
.glow {{ fill: #fff; opacity: 0; animation: glow 4.5s ease-in-out infinite; }}
@keyframes glow {{ 0%, 30%, 100% {{ opacity: 0; }} 12% {{ opacity: 0.55; }} }}
.select, .tag {{ transform-box: fill-box; transform-origin: center; }}
.select {{ animation: mark-select 7s cubic-bezier(.65, 0, .35, 1) infinite; }}
.tag {{ animation: mark-tag 7s cubic-bezier(.65, 0, .35, 1) infinite; }}
@keyframes mark-select {{ 0%, 55%, 100% {{ transform: scale(1); }} 70%, 80% {{ transform: scale(.82); }} }}
@keyframes mark-tag {{ 0%, 62%, 100% {{ transform: scale(1); }} 74% {{ transform: scale(1.12); }} 82% {{ transform: scale(1); }} }}
@media (prefers-reduced-motion: reduce) {{ .glow, .select, .tag {{ animation: none; }} }}
</style>
<clipPath id="window"><rect width="{w}" height="{h}" rx="8"/></clipPath>
<g clip-path="url(#window)">
<rect width="{w}" height="{h}" fill="{BG}"/>
<image x="0" y="34" width="{w}" height="{h - 34}" href="data:image/png;base64,{data}"/>
{glow}
{live_logo(img, k, ink)}
{title_bar(name, w)}
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" fill="none" stroke="{BORDER}"/>
</svg>
"""


def build(p):
    rows = [f'<text x="24" y="62" font-size="15" font-weight="700" fill="{WHITE}">{escape(p["name"])}</text>']
    label, colour = p["status"]
    rows.append(f'<circle cx="{W - 24 - len(label) * CHAR_W - 12}" cy="57" r="4" fill="{colour}"/>'
                f'<text x="{W - 24}" y="62" text-anchor="end" fill="{colour}">{escape(label)}</text>')
    for i, (key, value) in enumerate(p["facts"]):
        rows.append(f'<text x="24" y="{92 + i * 21}"><tspan fill="{WHITE}" font-weight="700">{escape(key)}:</tspan> '
                    f'<tspan fill="{GREEN}">{escape(value)}</tspan></text>')
    base = 248
    if p["bars"]:  # open tasks per person, the app's own work-balance view: one left (empty), one joined (yellow)
        for i, n in enumerate(p["bars"]):
            x, h = 24 + i * 20, max(n, 1) * 5
            fill, stroke = (YELLOW if i == len(p["bars"]) - 1 else BLUE, "none") if n else ("none", GREY)
            rows.append(f'<rect x="{x}" y="{base - h}" width="13" height="{h}" rx="1.5" fill="{fill}" stroke="{stroke}"/>')
        rows.append(f'<text x="{24 + len(p["bars"]) * 20 + 8}" y="{base - 24}" fill="{GREY}">open tasks per person</text>'
                    f'<text x="{24 + len(p["bars"]) * 20 + 8}" y="{base - 6}" fill="{GREY}">one left, one joined</text>')
    if p.get("flow"):  # the pipeline as boxes and arrows
        x = 24
        for i, step in enumerate(p["flow"]):
            w = len(step) * CHAR_W + 20
            rows.append(f'<rect x="{x}" y="{base - 30}" width="{w:.1f}" height="28" rx="4" fill="{BOX}" stroke="{GREY}" stroke-width="0.8"/>'
                        f'<text x="{x + w / 2:.1f}" y="{base - 11}" text-anchor="middle" fill="{BLUE if i == len(p["flow"]) - 1 else WHITE}">{escape(step)}</text>')
            x += w
            if i < len(p["flow"]) - 1:
                rows.append(f'<text x="{x + 6:.1f}" y="{base - 11}" fill="{GREY}">-&gt;</text>')
                x += 32

    prompt, prompt_y = "PS>", H - 24
    rows.append(f'<text x="24" y="{prompt_y}" fill="{GREY}">{prompt}</text>')
    text_x = 24 + (len(prompt) + 1) * CHAR_W
    typed, took, steps = typing(p["typed"], text_x, prompt_y, 0.5)
    total = took + 0.8
    key_times = ";".join(f"{t / total:.4f}" for t, _ in [(0, text_x)] + steps)
    xs = ";".join(f"{x:.1f}" for _, x in [(0, text_x)] + steps)
    cursor = (f'<rect x="{text_x:.1f}" y="{prompt_y + 2}" width="8" height="2" fill="{WHITE}">'
              f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>'
              f'<animate attributeName="x" calcMode="discrete" keyTimes="{key_times}" values="{xs}" '
              f'dur="{total:.2f}s" repeatCount="indefinite"/></rect>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-size="13" role="img" aria-label="{escape(p['name'])}: {escape(p['facts'][0][1])}">
<style>text {{ font-family: {FONT}; }}</style>
<rect width="{W}" height="{H}" rx="8" fill="{BG}" stroke="{BORDER}"/>
{title_bar(p['name'])}
<rect width="0" height="0"><animate id="cycle" attributeName="opacity" begin="0s;cycle.end" dur="{total:.2f}s" values="1"/></rect>
{''.join(rows)}
{typed}
{cursor}
</svg>
"""


if __name__ == "__main__":
    for theme in PALETTES:
        make_card.use_palette(theme)  # typing() reads make_card's colours
        make_card.use_palette(theme, globals())
        for p in PROJECTS:
            svg = build(p)
            xml.dom.minidom.parseString(svg)  # self-check: invalid XML would show as a broken image on GitHub
            out = ROOT / "assets" / f"project-{p['slug']}{SUFFIX[theme]}.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"wrote {out}")
        svg = banner("Data-Tagging-Application", *THESIS_PREVIEW[theme])
        xml.dom.minidom.parseString(svg)
        out = ROOT / "assets" / f"thesis-banner{SUFFIX[theme]}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
