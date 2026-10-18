"""Build assets/tech-stack.svg: skill icons that float gently, one after another.

Run:  python scripts/make_icons.py path/to/skill-icons/icons
(icons from https://github.com/tandpfun/skill-icons, MIT licence)
"""
import re
import sys
from pathlib import Path

ICONS = ["Python-Dark", "Flask-Dark", "MySQL-Dark", "SQLite", "Docker", "GithubActions-Dark",
         "Git", "Github-Dark", "HTML", "CSS", "JavaScript"]
PER_LINE = 6
CELL, SIZE = 300, 256  # same spacing as skillicons.dev
SHOWN_PX = 52          # on-screen width of one cell


def icon(path, n, x, y):
    body = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", Path(path).read_text(), flags=re.S)
    # several icons reuse the same ids (gradients, clips); prefix them so they don't clash
    body = re.sub(r'id="([^"]+)"', rf'id="i{n}-\1"', body)
    body = re.sub(r'url\(#([^)]+)\)', rf'url(#i{n}-\1)', body)
    body = re.sub(r'href="#([^"]+)"', rf'href="#i{n}-\1"', body)
    return (f'<g class="float" style="animation-delay:{n * 0.35:.2f}s">'
            f'<svg x="{x}" y="{y}" width="{SIZE}" height="{SIZE}" viewBox="0 0 256 256">{body}</svg></g>')


def build(folder):
    rows = -(-len(ICONS) // PER_LINE)
    width, height = PER_LINE * CELL - (CELL - SIZE), rows * CELL - (CELL - SIZE) + 24  # room to float
    parts = []
    for n, name in enumerate(ICONS):
        row, col = divmod(n, PER_LINE)
        left = (PER_LINE - min(PER_LINE, len(ICONS) - row * PER_LINE)) * CELL / 2  # centre a short last row
        parts.append(icon(Path(folder) / f"{name}.svg", n, left + col * CELL, 12 + row * CELL))
    scale = SHOWN_PX / CELL
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width * scale:.0f}" height="{height * scale:.0f}" viewBox="0 0 {width} {height}" role="img" aria-label="Python, Flask, MySQL, SQLite, Docker, GitHub Actions, Git, GitHub, HTML, CSS, JavaScript">
<!-- Icons: skill-icons by tandpfun, MIT licence, https://github.com/tandpfun/skill-icons -->
<style>
.float {{ animation: float 4s ease-in-out infinite; }}
@keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
@media (prefers-reduced-motion: reduce) {{ .float {{ animation: none; }} }}
</style>
{''.join(parts)}
</svg>
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/make_icons.py path/to/skill-icons/icons")
    svg = build(sys.argv[1])
    import xml.dom.minidom
    xml.dom.minidom.parseString(svg)  # self-check: invalid XML would show as a broken image on GitHub
    out = Path(__file__).resolve().parent.parent / "assets" / "tech-stack.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
