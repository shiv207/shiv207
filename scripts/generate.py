#!/usr/bin/env python3
# ─── GitHub Profile Card Generator ─────────────────────────────────────────
# Fetches live stats from the GitHub API and renders dark_mode.svg /
# light_mode.svg from scratch. The logo is read from scripts/logo.html and
# drawn as pixel-exact rects, so it doesn't depend on the viewer's fonts.
#
#   GITHUB_TOKEN=... python3 scripts/generate.py
# ────────────────────────────────────────────────────────────────────────────
import html
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "shiv207"
ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"

# ─── Content ───────────────────────────────────────────────────────────────
TAGLINES = [
    None,
    "[ Robotics Undergraduate ]",
    "[ AI × Robotics × Systems ]",
    None,
    "> Minimal systems.",
    "> Maximum impact.",
]

def sections(s):
    """Right-column layout. Each section is (title, [(key, value) | None])."""
    return [
        ("shiv@github", [
            ("OS", "Human (Reality)"),
            ("Role", "Robotics Undergraduate"),
            ("Repos", f"{s['repos']} public repositories"),
            ("Followers", f"{s['followers']} developers"),
            ("Editor", "Neovim 0.10 / zsh 5.9"),
            None,
            ("Languages", "C, C++, Python, TypeScript, JS"),
            ("Robotics", "ROS2, OpenCV, Gazebo, SLAM"),
            ("AI / ML", "PyTorch, Transformers, LangGraph"),
            ("Tools", "Linux, Docker, Git, Bash, Neovim"),
        ]),
        ("Projects", [
            ("VLA Simulation", "MuJoCo + LLM (SO-101 arm)"),
            ("MLX Voice Assistant", "Local Whisper + Gemma 3 4B"),
            ("AX-0 Reasoning", "Open o1-style CoT (Gemini)"),
            ("Deepsearch Clone", "Open source research agent"),
        ]),
        ("Contact", [
            ("GitHub", f"github.com/{USERNAME}"),
            ("LinkedIn", "linkedin.com/in/shivamsh-s-r"),
            ("Email", "shivamshsr@gmail.com"),
            ("Twitter", "x.com/RShivamsh"),
        ]),
        ("GitHub Stats", [
            [("Repos", fmt(s["repos"])), ("Stars", fmt(s["stars"]))],
            [("Commits", fmt(s["commits"])), ("Followers", fmt(s["followers"]))],
            ("Contributions (past year)", fmt(s["contributions"])),
        ]),
    ]

# ─── Themes ────────────────────────────────────────────────────────────────
THEMES = {
    "dark_mode.svg": {
        "bg": "#0d1117", "key": "#58a6ff", "value": "#e6edf3",
        "cc": "#8b949e", "title": "#d2a8ff", "tag": "#58a6ff",
        "logo": {},
    },
    "light_mode.svg": {
        "bg": "#ffffff", "key": "#0969da", "value": "#1f2328",
        "cc": "#656d76", "title": "#8250df", "tag": "#0969da",
        # white highlights would vanish on a white card
        "logo": {"#FFFFFF": "#d0d7de"},
    },
}

# ─── Layout ────────────────────────────────────────────────────────────────
WIDTH = 985
LINE_H = 20
TOP = 32
COL_X = 390        # right column
LINE_CHARS = 60    # text width of each right-column row
CELL_W, CELL_H = 7, 14
LOGO_X, LOGO_Y = 20, 22


# ─── GitHub API ────────────────────────────────────────────────────────────
def request(url, body=None):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("❌ GITHUB_TOKEN not set")
    req = urllib.request.Request(url, data=body and json.dumps(body).encode())
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_stats():
    print(f"⟳ Fetching stats for {USERNAME}...")
    user = request(f"{API}/users/{USERNAME}")

    stars, page = 0, 1
    while True:
        repos = request(f"{API}/users/{USERNAME}/repos?per_page=100&type=owner&page={page}")
        if not repos:
            break
        stars += sum(r["stargazers_count"] for r in repos)
        page += 1

    commits = request(f"{API}/search/commits?q=author:{USERNAME}&per_page=1")["total_count"]

    q = '{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions}}}}' % USERNAME
    gql = request(f"{API}/graphql", {"query": q})
    contributions = gql["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    stats = {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": stars,
        "commits": commits,
        "contributions": contributions,
    }
    for k, v in stats.items():
        print(f"  {k:<14}{v}")
    return stats


def fmt(n):
    return f"{n:,}"


# ─── Logo ──────────────────────────────────────────────────────────────────
SPAN = re.compile(r'<span style="([^"]*)">(.*?)</span>|(\n)', re.S)
# glyph -> (x, y, w, h) as fractions of a cell
GLYPHS = {
    "█": (0, 0, 1, 1),
    "▌": (0, 0, .5, 1),
    "▐": (.5, 0, .5, 1),
    "▀": (0, 0, 1, .5),
    "▄": (0, .5, 1, .5),
}


def parse_logo():
    """Return rows of (char, fg, bg) cells from the colored HTML art."""
    src = (ROOT / "scripts" / "logo.html").read_text()
    src = src[src.index(">", src.index("<pre")) + 1:src.index("</pre>")]
    rows, row = [], []
    for m in SPAN.finditer(src):
        if m.group(3):
            rows.append(row)
            row = []
            continue
        style = dict(
            p.split(":", 1) for p in m.group(1).replace(" ", "").split(";") if p
        )
        for ch in html.unescape(m.group(2)):
            row.append((ch, style.get("color"), style.get("background-color")))
    rows.append(row)
    return rows


def render_logo(rows, remap):
    rects = []
    for r, row in enumerate(rows):
        for c, (ch, fg, bg) in enumerate(row):
            x, y = LOGO_X + c * CELL_W, LOGO_Y + r * CELL_H
            if bg:
                rects.append((x, y, CELL_W, CELL_H, remap.get(bg, bg)))
            if ch in GLYPHS:
                gx, gy, gw, gh = GLYPHS[ch]
                rects.append((x + gx * CELL_W, y + gy * CELL_H,
                              gw * CELL_W, gh * CELL_H, remap.get(fg, fg)))
    return "\n".join(
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{f}"/>'
        for x, y, w, h, f in rects
    )


# ─── Text rows ─────────────────────────────────────────────────────────────
def kv(key, value, width):
    """'. Key: ...... value' padded with dots to exactly `width` chars."""
    dots = width - len(key) - len(value) - 5
    return (f'<tspan class="cc">. </tspan><tspan class="key">{escape(key)}</tspan>:'
            f'<tspan class="cc"> {"." * max(dots, 1)} </tspan>'
            f'<tspan class="value">{escape(value)}</tspan>')


def row_markup(item):
    if item is None:
        return '<tspan class="cc">. </tspan>'
    if isinstance(item, list):  # two kv pairs side by side
        (k1, v1), (k2, v2) = item
        half = (LINE_CHARS - 3) // 2
        return f"{kv(k1, v1, half)} | {kv(k2, v2, LINE_CHARS - 3 - half)}"
    return kv(*item, LINE_CHARS)


def header_markup(title, first):
    rule = "—" * (LINE_CHARS - len(title) - 2)
    cls = "" if first else ' class="title"'
    name = escape(title) if first else f"- {escape(title)}"
    rule = rule if first else rule[2:]
    return f"<tspan{cls}>{name}</tspan> -{rule}"


def render(stats, theme):
    lines = []
    for i, (title, items) in enumerate(sections(stats)):
        if i:
            lines.append(row_markup(None))
        lines.append(header_markup(title, i == 0))
        lines.extend(row_markup(it) for it in items)

    height = TOP + (len(lines) - 1) * LINE_H + 28
    right = "\n".join(
        f'<tspan x="{COL_X}" y="{TOP + i * LINE_H}">{l}</tspan>' for i, l in enumerate(lines)
    )

    tag_y = LOGO_Y + len(parse_logo()) * CELL_H + 46
    left = "\n".join(
        f'<tspan x="27" y="{tag_y + i * LINE_H}">{escape(t)}</tspan>'
        for i, t in enumerate(TAGLINES) if t
    )

    t = theme
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="{WIDTH}px" height="{height}px" viewBox="0 0 {WIDTH} {height}" font-size="15px">
<style>
@font-face {{
src: local('Consolas'), local('Consolas Bold'), local('JetBrains Mono');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}}
.key {{fill: {t['key']};}}
.value {{fill: {t['value']};}}
.cc {{fill: {t['cc']};}}
.title {{fill: {t['title']}; font-weight: bold;}}
text, tspan {{white-space: pre;}}
</style>
<rect width="{WIDTH}px" height="{height}px" fill="{t['bg']}" rx="15"/>

<g shape-rendering="crispEdges">
{render_logo(parse_logo(), t['logo'])}
</g>

<text fill="{t['tag']}" font-size="14px">
{left}
</text>

<text fill="{t['value']}">
{right}
</text>
</svg>
"""


def main():
    stats = fetch_stats()
    for name, theme in THEMES.items():
        (ROOT / name).write_text(render(stats, theme))
        print(f"  ✓ {name}")
    print("✅ Done")


if __name__ == "__main__":
    main()
