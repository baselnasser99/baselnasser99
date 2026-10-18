"""Build assets/profile.svg: a Windows Terminal-style profile card with ASCII art of my face.

Run:  python scripts/make_card.py photo.png   (needs Pillow)

photo.png is a portrait whose background has been made transparent. It is
not kept in the repository; only the generated card is.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
USER = "basel@github"
FACTS = [
    ("Role", "MS Information Systems student"),
    ("Focus", "product management · IT consulting"),
    ("School", "Northeastern University, Vancouver (Jan 2027)"),
    ("Degree", "B.Sc. Computer Science Engineering, Pécs (HU)"),
    ("Thesis", "Data Tagging Application"),
    ("Stack.Backend", "python, flask, sqlalchemy"),
    ("Stack.Data", "mysql, sqlite, sql"),
    ("Stack.Delivery", "docker, github actions, pytest"),
    ("Languages", "english, arabic"),
    ("Contact", "linkedin.com/in/baselnasser"),
    ("Email", "baselnasser99@gmail.com"),
    ("Email.School", "nasser.b@northeastern.edu"),
]
TYPED = ["open to co-op roles", "product · consulting · data", "let's build something useful"]
PROMPT = "PS C:\\Users\\basel>"

W, H = 900, 480
BG, BAR, RED, GREEN, BLUE, WHITE, GREY = "#0c0c0c", "#202020", "#f85149", "#39d353", "#58a6ff", "#e6edf3", "#a0a0a0"
FONT = "'Cascadia Mono', Consolas, ui-monospace, Menlo, 'Liberation Mono', monospace"
CHAR_W = 7.8  # width of one 13px monospace character
ART_BOX = (30, 50, 360, 360)  # x, y, width, height available for the face


def ascii_from_photo(path, cols=84):
    """Bright pixels become dense characters (the card is dark); transparent pixels become spaces."""
    from PIL import Image, ImageFilter, ImageOps

    ramp = " .,:;-=+*#%@"
    img = Image.open(path).convert("RGBA")
    img = img.crop(img.getbbox())
    img = img.crop((0, 0, img.width, int(img.height * 0.78)))  # head and shoulders: the face gets more characters
    rows = round(cols * img.height / img.width * 0.6 / 1.1)  # a character cell is 0.6 wide, 1.1 tall
    img = img.resize((cols, rows))
    grey = ImageOps.equalize(img.convert("L"), mask=img.getchannel("A"))  # spread the face's tones so eyes and beard show
    grey = ImageOps.autocontrast(grey.filter(ImageFilter.UnsharpMask(radius=1, percent=180, threshold=0)), cutoff=1)
    alpha = img.getchannel("A")
    return ["".join(ramp[1 + grey.getpixel((x, y)) * (len(ramp) - 2) // 255] if alpha.getpixel((x, y)) > 128 else " "
                    for x in range(cols)) for y in range(rows)]


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


def build(art):
    rows = []
    box_x, box_y, box_w, box_h = ART_BOX
    cols = max(len(line) for line in art)
    size = min(box_w / (cols * 0.6), box_h / (len(art) * 1.1))  # fit the face in its box
    char_w, line_h = size * 0.6, size * 1.1
    art_x = box_x + (box_w - cols * char_w) / 2
    art_y = box_y + (box_h - len(art) * line_h) / 2 + size
    for i, line in enumerate(art):
        rows.append(f'<text x="{art_x:.1f}" y="{art_y + i * line_h:.1f}" font-size="{size:.2f}" fill="{GREEN}" '
                    f'xml:space="preserve">{escape(line)}</text>')

    info_x = 420
    rows.append(f'<text x="{info_x}" y="74" font-size="16" font-weight="700" fill="{RED}">{USER}</text>')
    rows.append(f'<line x1="{info_x}" y1="84" x2="{W - 30}" y2="84" stroke="{RED}" stroke-width="1"/>')
    for i, (key, value) in enumerate(FACTS):
        rows.append(f'<text x="{info_x}" y="{106 + i * 20}" font-size="13">'
                    f'<tspan fill="{WHITE}" font-weight="700">{escape(key)}:</tspan> '
                    f'<tspan fill="{GREEN}">{escape(value)}</tspan></text>')
    swatch_y = 106 + len(FACTS) * 20 - 4
    for i, colour in enumerate(["#21262d", RED, "#3fb950", "#d29922", BLUE, "#bc8cff", "#39c5cf", WHITE]):
        rows.append(f'<rect x="{info_x + i * 26}" y="{swatch_y}" width="18" height="18" rx="2" fill="{colour}"/>')

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
<rect width="{W}" height="{H}" rx="8" fill="{BG}" stroke="#3a3a3a"/>
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
    svg = build(ascii_from_photo(sys.argv[1]))
    import xml.dom.minidom
    xml.dom.minidom.parseString(svg)  # self-check: invalid XML would show as a broken image on GitHub
    out = ROOT / "assets" / "profile.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out}")
