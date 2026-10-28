"""Build assets/tech-stack*.svg (my tools by folder, one-colour logos that float gently) and assets/focus*.svg
(the three things I do, as green tags that pop in one after another).

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
FOCUS = ["Product Management", "IT Consulting", "Data Analysis"]
# (text, tag fill, tag border) per theme: the card's green on GitHub's own code-block greys
FOCUS_THEMES = {"focus": ("#56d364", "#161b22", "#30363d"), "focus-light": ("#116329", "#f6f8fa", "#d0d7de")}
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


def focus(ink, fill, border, size=15, pad=14, gap=12, h=34):
    char = size * 0.6  # monospace advance
    widths = [len(t) * char + 2 * pad for t in FOCUS]
    w = sum(widths) + gap * (len(FOCUS) - 1) + 4
    tags, x = [], 2
    for i, (text, tw) in enumerate(zip(FOCUS, widths)):
        tags.append(f'<g class="pop" style="animation-delay:{0.15 + i * 0.18:.2f}s">'
                    f'<rect x="{x:.1f}" y="2" width="{tw:.1f}" height="{h}" rx="7" fill="{fill}" stroke="{border}"/>'
                    f'<text x="{x + tw / 2:.1f}" y="{2 + h / 2 + size * 0.35:.1f}" text-anchor="middle" fill="{ink}" font-weight="600">{escape(text)}</text></g>')
        x += tw + gap
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h + 4}" width="{w:.0f}" height="{h + 4}" font-size="{size}" role="img" aria-label="{escape(', '.join(FOCUS))}">
<style>
text {{ font-family: {FONT}; }}
.pop {{ transform-box: fill-box; transform-origin: center; animation: pop 0.5s cubic-bezier(.3, 1.4, .5, 1) both; }}
@keyframes pop {{ from {{ opacity: 0; transform: scale(0.6); }} to {{ opacity: 1; transform: scale(1); }} }}
@media (prefers-reduced-motion: reduce) {{ .pop {{ animation: none; }} }}
</style>
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
    for name, colours in FOCUS_THEMES.items():
        svg = focus(*colours)
        xml.dom.minidom.parseString(svg)
        out = ROOT / "assets" / f"{name}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out}")
