"""Build assets/tech-stack*.svg (my tools by folder, one-colour logos that float gently) and assets/header*.svg
(my name typed out in the terminal's type, with the three things I do as small tags under it).

Run:  python scripts/make_icons.py path/to/simple-icons/icons
(icons from https://github.com/simple-icons/simple-icons, CC0)

The background is transparent, so there is one file per GitHub theme; the README picks with <picture>.
"""
import re
import sys
import xml.dom.minidom
from pathlib import Path
from xml.sax.saxutils import escape

from make_card import FONT, ROOT

GROUPS = [
    ("build", [("python", "python"), ("flask", "flask"), ("sqlalchemy", "sqlalchemy"), ("javascript", "javascript")]),
    ("data", [("mysql", "mysql"), ("sqlite", "sqlite"), ("googlebigquery", "bigquery"), ("dbt", "dbt")]),
    ("ship", [("docker", "docker"), ("githubactions", "github actions"), ("pytest", "pytest"), ("netlify", "netlify")]),
]
# (logo, tool name, folder name) per theme: GitHub's own greens, inks and blues
THEMES = {"tech-stack": ("#56d364", "#e6edf3", "#58a6ff"), "tech-stack-light": ("#116329", "#1f2328", "#0969da")}
NAME, FOCUS = "Basel Nasser", ["Product Management", "IT Consulting", "Data Analysis"]
# (name, cursor and tag text, tag border) per theme: the cards' ink and green
HEADER_THEMES = {"header": ("#e6edf3", "#56d364", "#2f4a35"), "header-light": ("#1f2328", "#116329", "#b7d3bf")}
W, ROW, ICON = 900, 62, 30
LABEL_W, ITEM_W = 150, 182


def icon_path(folder, slug):
    return re.search(r'<path d="([^"]+)"', Path(folder, f"{slug}.svg").read_text(encoding="utf-8")).group(1)


def build(folder, logo, ink, accent):
    height = len(GROUPS) * ROW
    rows, n = [], 0
    for r, (group, items) in enumerate(GROUPS):
        y = 10 + r * ROW
        rows.append(f'<text x="24" y="{y + 21}" fill="{accent}" font-weight="700">{escape(group)}/</text>')
        for c, (slug, label) in enumerate(items):
            x = 24 + LABEL_W + c * ITEM_W
            scale = ICON / 24  # simple-icons are drawn on a 24px grid
            rows.append(f'<g class="float" style="animation-delay:{n * 0.3:.1f}s">'
                        f'<path transform="translate({x} {y}) scale({scale:.3f})" fill="{logo}" d="{icon_path(folder, slug)}"/></g>'
                        f'<text x="{x + ICON + 12}" y="{y + 21}" fill="{ink}" font-weight="600">{escape(label)}</text>')
            n += 1
    names = ", ".join(label for _, items in GROUPS for _, label in items)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" font-size="15" role="img" aria-label="Tech stack: {escape(names)}">
<!-- Logos: Simple Icons, CC0, https://github.com/simple-icons/simple-icons -->
<style>
text {{ font-family: {FONT}; }}
.float {{ animation: float 4s ease-in-out infinite; }}
@keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} }}
@media (prefers-reduced-motion: reduce) {{ .float {{ animation: none; }} }}
</style>
{''.join(rows)}
</svg>
"""


def header(ink, green, border, name_size=40, tag_size=13, w=560):
    """One sequence: the name types out once, the cursor starts blinking, then the tags appear."""
    advance = 0.6  # monospace advance, as a share of the font size
    per_char, typed = 0.07, len(NAME) * 0.07 + 0.25
    letters = "".join(f'<tspan class="type" style="animation-delay:{0.2 + i * per_char:.2f}s">{escape(ch)}</tspan>' for i, ch in enumerate(NAME))
    # the cursor is a character of the line, so it sits after the last letter whatever font the viewer has
    cursor = f'<tspan class="cursor" fill="{green}" style="animation-delay:{0.2 + typed:.2f}s, {0.2 + typed:.2f}s">_</tspan>'
    pad, gap, th, ty = 10, 8, 24, 72
    widths = [len(t) * tag_size * advance + 2 * pad for t in FOCUS]
    x = (w - sum(widths) - gap * (len(FOCUS) - 1)) / 2
    tags = []
    for i, (text, tw) in enumerate(zip(FOCUS, widths)):
        tags.append(f'<g class="tag" style="animation-delay:{0.45 + typed + i * 0.12:.2f}s">'
                    f'<rect x="{x:.1f}" y="{ty}" width="{tw:.1f}" height="{th}" rx="5" fill="none" stroke="{border}"/>'
                    f'<text x="{x + tw / 2:.1f}" y="{ty + th / 2 + tag_size * 0.35:.1f}" text-anchor="middle" font-size="{tag_size}" fill="{green}">{escape(text)}</text></g>')
        x += tw + gap
    h = ty + th + 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(NAME)}: {escape(', '.join(FOCUS))}">
<style>
text {{ font-family: {FONT}; }}
.type {{ fill-opacity: 0; animation: type 0.01s linear forwards; }}  /* tspans take fill-opacity, not opacity */
.cursor {{ fill-opacity: 0; animation: type 0.01s linear forwards, blink 1.1s steps(1) infinite; }}
.tag {{ opacity: 0; animation: rise 0.6s cubic-bezier(.16, 1, .3, 1) forwards; }}
@keyframes show {{ to {{ opacity: 1; }} }}
@keyframes type {{ to {{ fill-opacity: 1; }} }}
@keyframes blink {{ 50% {{ fill-opacity: 0; }} }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{ .type, .cursor {{ fill-opacity: 1; animation: none; }} .tag {{ opacity: 1; animation: none; }} }}
</style>
<text x="{w / 2}" y="48" text-anchor="middle" font-size="{name_size}" font-weight="700" fill="{ink}" letter-spacing="-0.5">{letters}{cursor}</text>
{''.join(tags)}
</svg>
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/make_icons.py path/to/simple-icons/icons")
    for name, colours in THEMES.items():
        svg = build(sys.argv[1], *colours)
        xml.dom.minidom.parseString(svg)  # self-check: invalid XML would show as a broken image on GitHub
        out = ROOT / "assets" / f"{name}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    for name, colours in HEADER_THEMES.items():
        svg = header(*colours)
        xml.dom.minidom.parseString(svg)
        out = ROOT / "assets" / f"{name}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out}")
