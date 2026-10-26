"""Build assets/tech-stack.svg and tech-stack-light.svg: my tools by folder, one-colour logos that float gently.

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
    ("build", [("python", "python"), ("flask", "flask"), ("sqlalchemy", "sqlalchemy")]),
    ("data", [("mysql", "mysql"), ("sqlite", "sqlite"), ("googlebigquery", "bigquery"), ("dbt", "dbt")]),
    ("ship", [("docker", "docker"), ("githubactions", "github actions"), ("pytest", "pytest")]),
]
# (logo, tool name, folder name) per theme: GitHub's own greens, inks and blues
THEMES = {"tech-stack": ("#56d364", "#e6edf3", "#58a6ff"), "tech-stack-light": ("#116329", "#1f2328", "#0969da")}
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/make_icons.py path/to/simple-icons/icons")
    for name, colours in THEMES.items():
        svg = build(sys.argv[1], *colours)
        xml.dom.minidom.parseString(svg)  # self-check: invalid XML would show as a broken image on GitHub
        out = ROOT / "assets" / f"{name}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
