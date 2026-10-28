"""Build assets/project-*.svg and thesis-banner*.svg: terminal windows for each project, matching profile.svg.

Run:  python scripts/make_project_cards.py   (needs numpy and network access, for VanScene's data)
"""
import xml.dom.minidom
from pathlib import Path
from xml.sax.saxutils import escape

import make_card
from make_card import BAR, BG, BLUE, BORDER, BOX, CHAR_W, FONT, GREEN, flag, GREY, PALETTES, ROOT, SUFFIX, WHITE, YELLOW, typing

W, H = 440, 290
THESIS = {
    "facts": [
        ("What", "fair split of labelling work"),
        ("Rebalance", "live, as people come and go"),
        ("Export", "csv, json, majority answer, kappa"),
        ("Stack", "flask, mysql, docker"),
        ("Tests", "300+ passing, ~94% coverage"),
        ("Thesis", "b.sc., university of pécs"),
    ],
    "status": ("shipped", "GREEN"),
    "typed": "open open-tasks --per-person",
    # the app's work-balance view after one person leaves and one joins (from docs/preview in the thesis repo):
    # (name, open tasks they already had, tasks moved to them, note)
    "balance": [
        ("Amira Haddad", 6, 2, ""), ("Lucas Martín", 6, 1, ""), ("Priya Nair", 7, 1, ""),
        ("Tomás García", 5, 2, ""), ("Hannah Weber", 6, 2, ""),
        ("Kenji Sato", 0, 0, "left the group"), ("Daniel Brooks", 0, 7, "just joined"),
    ],
}
TAG_YELLOW, TAG_INK = "#F5CF3A", "#1C2733"  # the app's own highlight yellow and the ink it sits under
VANSCENE_DATA = "https://raw.githubusercontent.com/baselnasser99/Datathon-Project/HEAD/web/data.json"
# the city's outline: its 22 local areas and its parks, City of Vancouver Open Data (Open Government Licence - Vancouver)
_OPEN_DATA = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/{}/exports/geojson"
CITY_AREAS, CITY_PARKS = _OPEN_DATA.format("local-area-boundary"), _OPEN_DATA.format("parks-polygon-representation")
# VanScene's heat scale, fewer to more: amber to plum on light, amber to rose on dark so the top end stays visible
HEAT = {"dark": ((242, 184, 75), (214, 76, 128)), "light": ((240, 178, 70), (110, 40, 96))}
PROJECTS = [
    {
        "slug": "vanscene",
        "name": "VanScene",
        "facts": [
            ("What", "crime map, plain words"),
            ("Award", "1st place, datathon"),
            ("Mine", "ui, data, a11y rebuild"),
            ("Data", "375k reports, weekly"),
            ("Stack", "js, leaflet, python"),
        ],
        "status": ("live", "GREEN"),
        "typed": "open vanscene --compare A B",
        "heat": True,  # a pixel heat map of the city, drawn from the app's own data
    },
    {
        "slug": "second-order",
        "name": "second-order",
        "facts": [
            ("Question", "why don't customers buy twice?"),
            ("Data", "olist marketplace, 9 tables"),
            ("Built", "staging + 3 marts, tested in ci"),
            ("Now", "180-day return by first order"),
            ("Stack", "bigquery, dbt, sql, python"),
        ],
        "status": ("in progress", "YELLOW"),
        "typed": "dbt build --select dim_customers",
        "flow": ["9 csv files", "bigquery", "dbt", "insight"],
        "flow_done": 3,  # steps finished so far; the rest are drawn dashed
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


def logo(x, y):
    """The app's logo: brackets that close in on a yellow square and let go, like an item being tagged (app.css)."""
    return (f'<g transform="translate({x} {y})">'
            f'<path class="select" d="M2 9V2h7M19 2h7v7M26 19v7h-7M9 26H2v-7" fill="none" stroke="{WHITE}" stroke-width="2.5" stroke-linecap="square"/>'
            f'<rect class="tag" x="10" y="10" width="8" height="8" rx="1" fill="{TAG_YELLOW}"/></g>')


def balance_chart(x, y):
    """Open tasks per person, drawn as the app draws them: blue for tasks they had, yellow for tasks moved to them.
    The moved ones glow row by row, as if they were being handed out again."""
    out = [f'<text x="{x}" y="{y}" font-weight="700" fill="{WHITE}">open tasks per person</text>'
           f'<text x="{x + 406}" y="{y}" text-anchor="end" fill="{GREY}">one left, one joined</text>']
    for row, (person, had, moved, note) in enumerate(THESIS["balance"]):
        ty = y + 30 + row * 22
        out.append(f'<text x="{x}" y="{ty}" fill="{GREY if note == "left the group" else WHITE}">{escape(person)}</text>')
        if note == "left the group":
            out.append(f'<path d="M{x} {ty - 4.5}h{len(person) * CHAR_W:.1f}" stroke="{GREY}"/>')
        for i in range(max(had + moved, 8 if not had + moved else 0)):
            sx, sy = x + 120 + i * 15, ty - 11
            if i >= had + moved:
                out.append(f'<rect x="{sx + .5}" y="{sy + .5}" width="11" height="11" rx="2" fill="none" stroke="{GREY}"/>')
                continue
            fill = BLUE if i < had else TAG_YELLOW
            out.append(f'<rect x="{sx}" y="{sy}" width="12" height="12" rx="2" fill="{fill}"/>')
            if i >= had:
                out.append(f'<rect class="glow" style="animation-delay:{row * 0.18:.2f}s" x="{sx}" y="{sy}" width="12" height="12" rx="2"/>')
        out.append(f'<text x="{x + 252}" y="{ty}" font-weight="700" fill="{WHITE}">{had + moved}</text>')
        if note:
            out.append(f'<text x="{x + 272}" y="{ty}" fill="{YELLOW if moved else GREY}">{escape(note)}</text>')
    fy = y + 30 + len(THESIS["balance"]) * 22 + 6
    out.append(f'<rect x="{x}" y="{fy - 9}" width="9" height="9" rx="2" fill="{BLUE}"/><text x="{x + 15}" y="{fy}" fill="{GREY}">open</text>'
               f'<rect x="{x + 62}" y="{fy - 9}" width="9" height="9" rx="2" fill="{TAG_YELLOW}"/><text x="{x + 77}" y="{fy}" fill="{GREY}">moved to them</text>'
               f'<text x="{x + 406}" y="{fy}" text-anchor="end" fill="{GREY}">busiest vs. lightest: <tspan font-weight="700" fill="{WHITE}">1 task</tspan></text>')
    return "".join(out)


def banner(name, w=900):
    """The thesis in a terminal window: what it does on the left, its work-balance view on the right,
    and the facts and a prompt underneath."""
    label, colour = THESIS["status"][0], globals()[THESIS["status"][1]]
    foot = 300  # top of the facts panel
    h = foot + 134
    facts = THESIS["facts"]
    half = (len(facts) + 1) // 2  # two columns: the app on the left, how it is built on the right
    left = (logo(24, 56)
            + f'<circle cx="68" cy="70" r="4" fill="{colour}"/><text x="78" y="75" fill="{colour}">{escape(label)}</text>'
            + f'<text x="24" y="134" font-size="30" font-weight="700" fill="{WHITE}">Labelling work,</text>'
            + f'<rect x="{24 + 7 * 18}" y="148" width="{6 * 18 + 8}" height="38" rx="3" fill="{TAG_YELLOW}"/>'
            + f'<text x="24" y="176" font-size="30" font-weight="700" fill="{WHITE}">shared <tspan fill="{TAG_INK}" dx="4">fairly</tspan><tspan dx="4">.</tspan></text>'
            + "".join(f'<text x="24" y="{222 + i * 20}" fill="{GREY}">{escape(t)}</text>' for i, t in enumerate(
                ["Images and audio are split into tasks and", "handed to whoever has the lightest load,",
                 "even as people join or leave mid-project."])))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-size="13" role="img" aria-label="{escape(name)}: labelling work, shared fairly. Open tasks per person stay within one task of each other after one person leaves and another joins.">
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
<rect width="{w}" height="{h}" rx="8" fill="{BG}" stroke="{BORDER}"/>
{title_bar(name, w)}
{left}
{balance_chart(w - 24 - 406, 74)}
<path d="M0 {foot}h{w}" stroke="{BORDER}"/>
{"".join(fact(key, value, 24 if i < half else w // 2 + 12, foot + 34 + (i % half) * 22) for i, (key, value) in enumerate(facts))}
{flag("hu", w // 2 + 12 + (len("Thesis: b.sc., university of pécs") + 1) * CHAR_W, foot + 34 + 2 * 22 - 10)}
{prompt_line(THESIS["typed"], h - 22)}
</svg>
"""


_points = None


def _rings(url, keep=lambda props: True):
    """The outer ring of every polygon in a GeoJSON feed, as (lng, lat) lists."""
    import json, urllib.request

    for feat in json.load(urllib.request.urlopen(url, timeout=60))["features"]:
        geom = feat["geometry"]
        if geom and keep(feat["properties"]):
            yield from (poly[0] for poly in ([geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]))


def heat_map(theme, x0, y0, cols=32, width=168):
    """Vancouver as pixels, coloured by reported incidents, that pop in from the busiest spot outward and fade,
    on a loop. Counts come from VanScene's web/data.json (coordinates in 1e-4 degrees). The city's local areas and
    Stanley Park give the outline; inside it, a cell with no reports and no park is water (False Creek, the coast)."""
    import json, math, urllib.request
    import numpy as np
    from PIL import Image, ImageDraw

    global _points
    if _points is None:
        _points = json.load(urllib.request.urlopen(VANSCENE_DATA, timeout=60))["points"]
    parks = list(_rings(CITY_PARKS))
    city = list(_rings(CITY_AREAS)) + list(_rings(CITY_PARKS, lambda p: p["park_name"] == "Stanley Park"))
    allpts = np.array([pt for ring in city for pt in ring])
    (ln0, la0), (ln1, la1) = allpts.min(0), allpts.max(0)
    rows = math.ceil((la1 - la0) / ((ln1 - ln0) / cols * math.cos(math.radians(49.25))))  # square pixels on the ground
    pitch = width / cols

    def cover(rings, ss=8):
        """How much of each pixel the polygons cover, 0 to 255 (drawn at 8x, then averaged)."""
        mask = Image.new("L", (cols * ss, rows * ss))
        draw = ImageDraw.Draw(mask)
        for ring in rings:
            draw.polygon([((lng - ln0) / (ln1 - ln0) * cols * ss, (la1 - lat) / (la1 - la0) * rows * ss) for lng, lat in ring], fill=255)
        return np.asarray(mask.resize((cols, rows), Image.BOX))

    lat = (_points["lat0"] + np.array(_points["lat"])) / 1e4
    lng = (_points["lng0"] + np.array(_points["lng"])) / 1e4
    grid, _, _ = np.histogram2d(la1 - lat, lng - ln0, bins=[rows, cols], range=[[0, la1 - la0], [0, ln1 - ln0]])
    land = (cover(city) > 110) & ((grid > 0) | (cover(parks) > 128))
    busy = land & (grid >= 30)  # streets with real reports; parks and quiet land are drawn dim
    level = np.searchsorted(np.sort(grid[busy]), grid) / busy.sum()  # rank, so every neighbourhood gets a shade
    peak = np.unravel_index(np.where(busy, grid, 0).argmax(), grid.shape)
    lo, hi = HEAT[theme]
    out = []
    for (r, c), t in np.ndenumerate(level):
        if not land[r, c]:
            continue
        rgb = "#%02x%02x%02x" % tuple(round(a + (b - a) * t) for a, b in zip(lo, hi)) if busy[r, c] else BORDER
        delay = math.hypot(r - peak[0], c - peak[1]) * 0.05
        out.append(f'<rect class="px" style="animation-delay:{delay:.2f}s" x="{x0 + c * pitch:.1f}" y="{y0 + r * pitch:.1f}" '
                   f'width="{pitch - 1:.1f}" height="{pitch - 1:.1f}" rx="1" fill="{rgb}"/>')
    return "".join(out)


def prompt_line(text, y):
    """PS> and a command that types out, with a blinking cursor that follows it (SMIL, restarted by #cycle)."""
    x = 24 + 4 * CHAR_W
    typed, took, steps = typing(text, x, y, 0.5)
    total = took + 0.8
    key_times = ";".join(f"{t / total:.4f}" for t, _ in [(0, x)] + steps)
    xs = ";".join(f"{cx:.1f}" for _, cx in [(0, x)] + steps)
    return (f'<rect width="0" height="0"><animate id="cycle" attributeName="opacity" begin="0s;cycle.end" dur="{total:.2f}s" values="1"/></rect>'
            f'<text x="24" y="{y}" fill="{GREY}">PS&gt;</text>{typed}'
            f'<rect x="{x:.1f}" y="{y + 2}" width="8" height="2" fill="{WHITE}">'
            f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>'
            f'<animate attributeName="x" calcMode="discrete" keyTimes="{key_times}" values="{xs}" dur="{total:.2f}s" repeatCount="indefinite"/></rect>')


def fact(key, value, x, y):
    return (f'<text x="{x}" y="{y}"><tspan fill="{WHITE}" font-weight="700">{escape(key)}:</tspan> '
            f'<tspan fill="{GREEN}">{escape(value)}</tspan></text>')


def build(p, theme):
    label, colour = p["status"][0], globals()[p["status"][1]]  # by name, so each theme gets its own shade
    rows = [f'<text x="24" y="62" font-size="15" font-weight="700" fill="{WHITE}">{escape(p["name"])}</text>'
            f'<circle cx="{W - 24 - len(label) * CHAR_W - 12}" cy="57" r="4" fill="{colour}"/>'
            f'<text x="{W - 24}" y="62" text-anchor="end" fill="{colour}">{escape(label)}</text>']
    rows += [fact(key, value, 24, 92 + i * 21) for i, (key, value) in enumerate(p["facts"])]
    base = 248
    if p.get("heat"):
        rows.append(heat_map(theme, W - 24 - 168, 80))
        lo, hi = HEAT[theme]
        key = [f'<text x="24" y="222" fill="{GREY}">fewer</text>']
        for i in range(6):
            rgb = "#%02x%02x%02x" % tuple(round(a + (b - a) * i / 5) for a, b in zip(lo, hi))
            key.append(f'<rect x="{24 + 6 * CHAR_W + i * 12:.1f}" y="212" width="10" height="10" rx="1.5" fill="{rgb}"/>')
        key.append(f'<text x="{24 + 6 * CHAR_W + 6 * 12 + 4:.1f}" y="222" fill="{GREY}">more</text>'
                   f'<rect x="{24 + 6 * CHAR_W + 6 * 12 + 4 + 5 * CHAR_W:.1f}" y="212" width="10" height="10" rx="1.5" fill="{BORDER}"/>'
                   f'<text x="{24 + 6 * CHAR_W + 6 * 12 + 4 + 5 * CHAR_W + 16:.1f}" y="222" fill="{GREY}">park</text>'
                   f'<text x="24" y="244" fill="{GREY}">since 2016, pixel ≈ 450 m</text>')
        rows.append("".join(key))
    if p.get("flow"):  # the pipeline as boxes and arrows
        x = 24
        for i, step in enumerate(p["flow"]):
            w = len(step) * CHAR_W + 20
            done = i < p.get("flow_done", len(p["flow"]))
            edge = f'stroke="{GREEN}"' if done else f'stroke="{GREY}" stroke-dasharray="3 3"'
            rows.append(f'<rect x="{x}" y="{base - 30}" width="{w:.1f}" height="28" rx="4" fill="{BOX}" {edge} stroke-width="0.8"/>'
                        f'<text x="{x + w / 2:.1f}" y="{base - 11}" text-anchor="middle" fill="{BLUE if i == len(p["flow"]) - 1 else WHITE}">{escape(step)}</text>')
            x += w
            if i < len(p["flow"]) - 1:
                rows.append(f'<text x="{x + 6:.1f}" y="{base - 11}" fill="{GREY}">-&gt;</text>')
                x += 32

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-size="13" role="img" aria-label="{escape(p['name'])}: {escape(p['facts'][0][1])}">
<style>
text {{ font-family: {FONT}; }}
.px {{ transform-box: fill-box; transform-origin: center; animation: blast 7s ease-out infinite both; }}
@keyframes blast {{ 0% {{ opacity: 0; transform: scale(0); }} 6% {{ opacity: 1; transform: scale(1.5); }} 12%, 85% {{ opacity: 1; transform: scale(1); }} 97%, 100% {{ opacity: 0; transform: scale(1); }} }}
@media (prefers-reduced-motion: reduce) {{ .px {{ animation: none; }} }}
</style>
<rect width="{W}" height="{H}" rx="8" fill="{BG}" stroke="{BORDER}"/>
{title_bar(p['name'])}
{''.join(rows)}
{prompt_line(p["typed"], H - 24)}
</svg>
"""


if __name__ == "__main__":
    for theme in PALETTES:
        make_card.use_palette(theme)  # typing() reads make_card's colours
        make_card.use_palette(theme, globals())
        for p in PROJECTS:
            svg = build(p, theme)
            xml.dom.minidom.parseString(svg)  # self-check: invalid XML would show as a broken image on GitHub
            out = ROOT / "assets" / f"project-{p['slug']}{SUFFIX[theme]}.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"wrote {out}")
        svg = banner("Data-Tagging-Application")
        xml.dom.minidom.parseString(svg)
        out = ROOT / "assets" / f"thesis-banner{SUFFIX[theme]}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
