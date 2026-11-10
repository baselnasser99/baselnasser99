"""Build assets/profile.svg: a Windows Terminal-style profile card with my face drawn as ASCII art.

Run:  python scripts/make_card.py photo.png   (needs Pillow, numpy and opencv-python)

photo.png is a portrait whose background has been made transparent, for example with
rembg's u2net_human_seg model and alpha matting (foreground 250, background 60, erode 25),
which keeps the curls without the night sky between them. It is not kept in the repository;
only the generated card is.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
USER = "basel@github"
FACTS = [
    ("Role", "MS Information Systems student"),
    ("Focus", "Product Management · IT Consulting · Data Analysis"),
    ("School", "Northeastern University, Vancouver (Jan 2027)"),
    ("Degree", "B.Sc. Computer Science Engineering, Pécs (HU)"),
    ("Thesis", "Data Tagging Application"),
    ("Stack.Build", "python, flask, sqlalchemy, javascript"),
    ("Stack.Data", "mysql, sqlite, bigquery, dbt"),
    ("Stack.Ship", "docker, github actions, pytest, netlify"),
    ("Languages", "english, arabic"),
    ("Contact", "linkedin.com/in/baselnasser"),
    ("Email", "baselnasser99@gmail.com"),
    ("Email.School", "nasser.b@northeastern.edu"),
]
NOW = ("Now", "second-order shipped, MS in 2027")
ROUTE = [("ps", "Palestine", "home"), ("hu", "Pécs, HU", "B.Sc."), ("ca", "Vancouver, CA", "MS, 2027")]
TYPED = ["product · consulting · data", "let's build something useful"]
PROMPT = "PS C:\\Users\\basel>"

W, H = 900, 480
# One palette per GitHub theme; WHITE is the main ink and ART the face, whatever the theme.
PALETTES = {
    "dark": dict(BG="#0c0c0c", BAR="#202020", RED="#c9735f", GREEN="#56d364", BLUE="#58a6ff", WHITE="#e6edf3",
                 GREY="#a0a0a0", YELLOW="#d29922", BORDER="#3a3a3a", BOX="#161b22", ART="#56d364"),
    "light": dict(BG="#f6f8fa", BAR="#eaeef2", RED="#cf222e", GREEN="#1a7f37", BLUE="#0969da", WHITE="#1f2328",
                  GREY="#6e7781", YELLOW="#9a6700", BORDER="#d0d7de", BOX="#eef1f4", ART="#1f2328"),
}
SUFFIX = {"dark": "", "light": "-light"}  # file name ending per theme


def use_palette(name, namespace=None):
    """Set the colour names in this module (or a module that imported them) to one theme's palette."""
    (namespace if namespace is not None else globals()).update(PALETTES[name])


BG = BAR = RED = GREEN = BLUE = WHITE = GREY = YELLOW = BORDER = BOX = ART = None  # filled by use_palette
use_palette("dark")
FONT = "'Cascadia Mono', Consolas, ui-monospace, Menlo, 'Liberation Mono', monospace"
CHAR_W = 7.8  # width of one 13px monospace character
ART_BOX = (30, 46, 360, 384)  # x, y, width, height available for the face


def drawn_face(path, theme, size=7.0, line_k=0.35, every=3):
    """The face as a drawing with real characters typed over it: the drawing carries the likeness, the characters
    keep it a terminal. Every `every` seconds it glitches: slices tear sideways and flash the same characters as
    digits, so the face is seen to be made of text.

    dark: light where the photo is light, like a lit screen. light: dark where the photo is dark, like a print.
    Returns SVG to place inside ART_BOX.
    """
    import base64, io
    import cv2
    import numpy as np
    from PIL import Image

    ss = 2  # the drawing is stored at 2x so the lines stay sharp
    box_x, box_y, box_w, box_h = ART_BOX
    img = Image.open(path).convert("RGBA")
    img = img.crop(img.getbbox())
    img = img.crop((0, 0, img.width, int(img.height * 0.80)))  # head and shoulders
    k = min(box_w / img.width, box_h / img.height) * ss
    img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    gray = np.asarray(img.convert("L"), float) / 255
    alpha = np.asarray(img.getchannel("A"), float) / 255
    h, w = gray.shape

    # pen lines (XDoG): ink wherever the photo darkens against its surroundings: curls, brows, eyes, lips, beard
    d = cv2.GaussianBlur(gray, (0, 0), 1.3) - 0.98 * cv2.GaussianBlur(gray, (0, 0), 1.3 * 1.6)
    lines = np.clip(np.where(d < -0.004, 1 - np.exp(d * 70), 0), 0, 1)
    face = gray[int(h * 0.08):int(h * 0.55)][alpha[int(h * 0.08):int(h * 0.55)] > 0.5]
    lo, hi = np.percentile(face, [3, 97])  # contrast set from the face only, so the white shirt clips instead of the eyes
    tone = np.clip((gray - lo) / (hi - lo), 0, 1)
    edge = np.clip(alpha - cv2.erode(alpha, np.ones((3, 3))), 0, 1)  # the silhouette, so ears and jaw keep an edge on paper
    edge = np.clip(cv2.GaussianBlur(edge, (0, 0), 0.8) * 2, 0, 1)
    yy, xx = np.mgrid[0:h, 0:w]
    oval = np.sqrt(((xx - w / 2) / (w * 0.52)) ** 2 + ((yy - h * 0.35) / (h * 0.78)) ** 2)
    alpha *= np.clip((1.05 - oval) / 0.25, 0, 1)  # shoulders dissolve at the bottom corners, the head is untouched
    lit = np.clip(tone + 0.8 * (tone - cv2.GaussianBlur(tone, (0, 0), 6 * ss)), 0, 1) ** 1.1  # local contrast keeps the curls
    if theme == "dark":  # light where the photo is light
        ink = np.clip(lit * 0.9 - lines * line_k, 0, 1) * alpha
    else:  # dark where the photo is dark, like a print
        ink = np.clip(np.maximum((1 - lit) ** 1.2 * 0.85 + lines * line_k, edge * 0.55), 0, 1) * alpha

    # on paper a strong drawing reads as a sketch, so there the characters carry most of the shading
    img_op, glyph_op, gmin = (0.8, 0.6, 0.15) if theme == "dark" else (0.4, 0.95, 0.07)
    char_w, line_h = size * 0.6, size * 1.1
    r, g, b = (int(ART[i:i + 2], 16) for i in (1, 3, 5))
    a = (ink * 255 * img_op).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(np.dstack([np.full_like(a, r), np.full_like(a, g), np.full_like(a, b), a]), "RGBA").save(buf, "PNG", optimize=True)
    x0, y0 = box_x + (box_w - w / ss) / 2, box_y + (box_h - h / ss) / 2
    image = (f'<image x="{x0:.1f}" y="{y0:.1f}" width="{w / ss:.1f}" height="{h / ss:.1f}" '
             f'href="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"/>')

    # real characters over the drawing, chosen from the same ink: symbols normally, digits in the glitch
    small = cv2.resize(ink, (int(w / ss / char_w), int(h / ss / line_h)), interpolation=cv2.INTER_AREA)

    def text(ramp):
        out = []
        for row, vals in enumerate(small):
            line = "".join(ramp[min(int(v * (len(ramp) - 1) * 1.15 + 0.35), len(ramp) - 1)] if v > gmin else " " for v in vals).rstrip()
            if line:
                out.append(f'<text x="{x0:.1f}" y="{y0 + (row + 0.82) * line_h:.1f}" xml:space="preserve">{escape(line)}</text>')
        return "".join(out)

    # the glitch: once per loop, for half a second, a few thin slices flicker into the same characters as digits,
    # twitching a little sideways, then snap back; the rest of the face is untouched. Slices come from a fixed seed,
    # so every run of this script draws the same glitch.
    rng = np.random.default_rng(7)
    fw, fh = w / ss, h / ss
    burst = 0.5 / every * 100  # share of the loop the glitch lasts
    css, slices = [], []
    for i in range(8):
        sh = float(rng.uniform(3, 16))
        sy = y0 + float(rng.uniform(0.05, 0.9)) * fh
        frames = sorted(rng.uniform(0, burst, 3))
        steps = " ".join(f"{t:.2f}% {{ opacity: 1; transform: translateX({float(rng.choice([-1, 1]) * rng.uniform(2, 6)):.1f}px); }}" for t in frames)
        css.append(f"@keyframes g{i} {{ 0% {{ opacity: 0; }} {steps} {frames[-1] + burst / 4:.2f}%, 100% {{ opacity: 0; transform: none; }} }}"
                   f".g{i} {{ animation: g{i} {every}s steps(1, end) infinite; }}")
        slices.append(f'<clipPath id="s{i}"><rect x="{x0 - 20:.1f}" y="{sy:.1f}" width="{fw + 40:.1f}" height="{sh:.1f}"/></clipPath>'
                      f'<g clip-path="url(#s{i})"><g class="gl g{i}"><rect x="{x0 - 20:.1f}" y="{sy:.1f}" width="{fw + 40:.1f}" height="{sh:.1f}" fill="{BG}"/><use href="#digits"/></g></g>')
    return (f'<style>.gl {{ opacity: 0; }} {"".join(css)}'
            '@media (prefers-reduced-motion: reduce) { .gl { animation: none; } }</style>'
            f'<defs><g id="face">{image}<g font-size="{size}" fill="{ART}" fill-opacity="{glyph_op}">{text(" .,:;-=+*#%@")}</g></g>'
            f'<g id="digits" font-size="{size}" fill="{ART}">{text(" .:174235968")}</g></defs>'
            f'<use href="#face"/>{"".join(slices)}')


def typing(text, x, y, start, per_char=0.09, hold=2.2):
    """One line that types out, holds, then disappears (SMIL, so it also runs inside an <img>)."""
    total = len(text) * per_char + hold
    out, steps = [], []
    for i, ch in enumerate(text):
        begin = start + i * per_char
        steps.append((begin, x + (i + 1) * CHAR_W))  # the cursor jumps as each letter appears
        out.append(f'<text x="{x + i * CHAR_W:.1f}" y="{y}" fill="{WHITE}" opacity="0">{escape(ch)}'
                   f'<set attributeName="opacity" to="1" begin="{begin:.2f}s;cycle.end+{begin:.2f}s" '
                   f'dur="{start + total - begin:.2f}s"/></text>')
    steps.append((start + total, x))
    return "".join(out), total, steps


def title_bar():
    """Windows Terminal: one tab on the left, minimise / maximise / close on the right."""
    tab = (f'<path d="M8 34V14a6 6 0 0 1 6-6h212a6 6 0 0 1 6 6v20z" fill="{BG}"/>'
           f'<text x="24" y="26" font-size="12" fill="{GREEN}" font-weight="700">&gt;_</text>'
           f'<text x="46" y="26" font-size="12" fill="{WHITE}">{USER}: ~</text>'
           f'<path d="M210 17l8 8m0-8l-8 8" stroke="{GREY}" stroke-width="1.2"/>'
           f'<path d="M250 15v12m-6-6h12" stroke="{GREY}" stroke-width="1.2"/>'
           f'<path d="M274 18l5 5 5-5" stroke="{GREY}" stroke-width="1.2" fill="none"/>')
    right = W - 46 * 3
    controls = (f'<path d="M{right + 17} 21h12" stroke="{WHITE}" stroke-width="1"/>'
                f'<rect x="{right + 46 + 17.5}" y="15.5" width="11" height="11" fill="none" stroke="{WHITE}" stroke-width="1"/>'
                f'<path d="M{right + 92 + 17} 15l11 11m0-11l-11 11" stroke="{WHITE}" stroke-width="1"/>')
    return (f'<path d="M8 0h{W - 16}a8 8 0 0 1 8 8v26H0V8a8 8 0 0 1 8-8z" fill="{BAR}"/>' + tab + controls)


def flag(name, x, y, w=18, h=12):
    """Tiny flat flags, drawn in SVG so no external images are needed."""
    if name == "ps":
        s = h / 3
        body = (f'<rect x="{x}" y="{y}" width="{w}" height="{s}" fill="#000"/>'
                f'<rect x="{x}" y="{y + s}" width="{w}" height="{s}" fill="#fff"/>'
                f'<rect x="{x}" y="{y + 2 * s}" width="{w}" height="{s}" fill="#007a3d"/>'
                f'<path d="M{x} {y}L{x + w / 2} {y + h / 2}L{x} {y + h}z" fill="#ce1126"/>')
    elif name == "hu":
        s = h / 3
        body = (f'<rect x="{x}" y="{y}" width="{w}" height="{s}" fill="#ce2939"/>'
                f'<rect x="{x}" y="{y + s}" width="{w}" height="{s}" fill="#fff"/>'
                f'<rect x="{x}" y="{y + 2 * s}" width="{w}" height="{s}" fill="#477050"/>')
    else:  # ca: red, white, red with a small leaf
        q = w / 4
        cx, cy = x + w / 2, y + h / 2
        body = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#d52b1e"/>'
                f'<rect x="{x + q}" y="{y}" width="{2 * q}" height="{h}" fill="#fff"/>'
                f'<path d="M{cx} {cy - 4}L{cx + 1.2} {cy - 1.5}L{cx + 3.5} {cy - 2.2}L{cx + 2.4} {cy + 0.5}L{cx + 3.2} {cy + 1.4}'
                f'L{cx + 0.5} {cy + 1.6}L{cx + 0.5} {cy + 4}L{cx - 0.5} {cy + 4}L{cx - 0.5} {cy + 1.6}L{cx - 3.2} {cy + 1.4}'
                f'L{cx - 2.4} {cy + 0.5}L{cx - 3.5} {cy - 2.2}L{cx - 1.2} {cy - 1.5}z" fill="#d52b1e"/>')
    return body + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{BORDER}" stroke-width="0.6"/>'


def route(y):
    """Home, then degree, then master's: flags on a dashed line, with a dot travelling along it."""
    xs = [455, 635, 815]
    out = [f'<path d="M{xs[0]} {y}H{xs[-1]}" stroke="{GREY}" stroke-width="1" stroke-dasharray="3 4"/>']
    for x, (code, place, note) in zip(xs, ROUTE):
        out.append(flag(code, x - 9, y - 26))
        out.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{BG}" stroke="{GREEN}" stroke-width="1.5"/>')
        out.append(f'<text x="{x}" y="{y + 20}" text-anchor="middle" fill="{WHITE}">{escape(place)}</text>')
        out.append(f'<text x="{x}" y="{y + 36}" text-anchor="middle" font-size="11" fill="{GREY}">{escape(note)}</text>')
    out.append(f'<circle r="3" fill="{GREEN}"><animateMotion path="M{xs[0]} {y}H{xs[-1]}" dur="5s" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="5s" repeatCount="indefinite"/></circle>')
    return "".join(out)


def build(face):
    rows = [face]

    info_x = 420
    rows.append(f'<text x="{info_x}" y="74" font-size="16" font-weight="700" fill="{WHITE}">{USER}</text>')
    rows.append(f'<line x1="{info_x}" y1="84" x2="{W - 30}" y2="84" stroke="{GREY}" stroke-width="1"/>')
    for i, (key, value) in enumerate(FACTS):
        rows.append(f'<text x="{info_x}" y="{106 + i * 20}" font-size="13">'
                    f'<tspan fill="{WHITE}" font-weight="700">{escape(key)}:</tspan> '
                    f'<tspan fill="{GREEN}">{escape(value)}</tspan></text>')
    status_y = 106 + len(FACTS) * 20
    key, value = NOW
    rows.append(f'<text x="{info_x}" y="{status_y}" font-size="13"><tspan fill="{WHITE}" font-weight="700">{escape(key)}:</tspan> '
                f'<tspan fill="{GREEN}">{escape(value)}</tspan></text>')
    dot_x = info_x + (len(key) + len(value) + 3) * CHAR_W
    rows.append(f'<circle cx="{dot_x:.1f}" cy="{status_y - 4.5}" r="4" fill="{YELLOW}">'
                f'<animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    rows.append(route(status_y + 46))

    prompt_y = H - 28
    rows.append(f'<text x="30" y="{prompt_y}" font-size="13" fill="{GREY}">{escape(PROMPT)}</text>')
    text_x = 30 + (len(PROMPT) + 1) * CHAR_W
    t, start, steps = [], 0.5, [(0, text_x)]
    for phrase in TYPED:
        svg, took, phrase_steps = typing(phrase, text_x, prompt_y, start)
        t.append(svg)
        steps += phrase_steps
        start += took + 0.3
    key_times = ";".join(f"{tm / start:.4f}" for tm, _ in steps)
    xs = ";".join(f"{x:.1f}" for _, x in steps)
    cursor = (f'<rect x="{text_x:.1f}" y="{prompt_y + 2}" width="8" height="2" fill="{WHITE}">'  # Windows-style underline cursor
              f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>'
              f'<animate attributeName="x" calcMode="discrete" keyTimes="{key_times}" values="{xs}" '
              f'dur="{start:.2f}s" repeatCount="indefinite"/></rect>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-size="13" role="img" aria-label="Basel Nasser: MS Information Systems student at Northeastern University, Vancouver, focused on product management and IT consulting">
<style>text {{ font-family: {FONT}; }}</style>
<rect width="{W}" height="{H}" rx="8" fill="{BG}" stroke="{BORDER}"/>
{title_bar()}
<rect width="0" height="0"><animate id="cycle" attributeName="opacity" begin="0s;cycle.end" dur="{start:.2f}s" values="1"/></rect>
{''.join(rows)}
{''.join(t)}
{cursor}
</svg>
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/make_card.py photo.png")
    import xml.dom.minidom
    for theme in PALETTES:
        use_palette(theme)
        svg = build(drawn_face(sys.argv[1], theme))
        xml.dom.minidom.parseString(svg)  # self-check: invalid XML would show as a broken image on GitHub
        out = ROOT / "assets" / f"profile{SUFFIX[theme]}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out}")
