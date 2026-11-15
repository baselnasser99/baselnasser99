"""Re-shade the Pac-Man contribution graph so one huge day can't wash out the rest.

GitHub shades contribution days against the busiest day, and the Pac-Man action copies those shades. This rewrites
each day's colour in the SVGs the action made, by the day's rank among my active days instead: the busiest quarter
gets the darkest green, the quietest quarter the lightest. The game itself is left alone.

Run:  python scripts/recolor_pacman.py dist   (standard library only; reads GITHUB_TOKEN, or asks the gh CLI)
The Pac-Man workflow runs it between drawing the graph and publishing it.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

USER = "baselnasser99"
QUERY = """query($login: String!) { user(login: $login) { contributionsCollection { contributionCalendar {
  weeks { contributionDays { date contributionCount } } } } } }"""
# GitHub's own greens, lightest to darkest, so the graph keeps its look
GREENS = {"light": ["#9be9a8", "#40c463", "#30a14e", "#216e39"], "dark": ["#0e4429", "#006d32", "#26a641", "#39d353"]}


def levels(counts):
    """0 for no contributions; otherwise 1-4 by rank among active days. Equal days share a level."""
    active = sorted(c for c in counts if c)
    return [1 + min(3, sum(a < c for a in active) * 4 // len(active)) if c else 0 for c in counts]


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
                                 {"Authorization": f"bearer {token}", "User-Agent": "profile-pacman-recolor"})
    data = json.load(urllib.request.urlopen(req, timeout=60))
    if "errors" in data:
        sys.exit(f"GitHub API error: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def cell_levels(weeks):
    """(week, weekday) -> level, in the action's cell ids: c-<week>-<weekday>, Sunday = 0."""
    days = [(col, (datetime.date.fromisoformat(d["date"]).weekday() + 1) % 7, d["contributionCount"])
            for col, week in enumerate(weeks) for d in week["contributionDays"]]
    return {(col, row): lv for (col, row, _), lv in zip(days, levels([n for _, _, n in days]))}


def recolor(svg, lv, greens):
    """Swap the colour each day starts with (and returns to) for its rank colour; count the cells changed."""
    changed = 0

    def swap(m):
        nonlocal changed
        level = lv.get((int(m["x"]), int(m["y"])), 0)
        if not level:
            return m[0]
        changed += 1
        old = m["vals"].split(";")[0]
        return m[0].replace(m["vals"], m["vals"].replace(old, greens[level - 1]))

    svg = re.sub(r'<rect id="c-(?P<x>\d+)-(?P<y>\d+)"[^>]*>\s*<animate[^>]*?values="(?P<vals>[^"]*)"', swap, svg)
    return svg, changed


if __name__ == "__main__":
    assert levels([0, 5, 224, 6, 7, 8]) == [0, 1, 4, 1, 2, 3]  # self-check: the 224 day doesn't stretch the scale
    lv = cell_levels(fetch())
    active = sum(1 for v in lv.values() if v)
    for path in Path(sys.argv[1] if len(sys.argv) > 1 else "dist").glob("pacman-contribution-graph*.svg"):
        theme = "dark" if path.stem.endswith("-dark") else "light"
        svg, changed = recolor(path.read_text(encoding="utf-8"), lv, GREENS[theme])
        if changed != active:  # every active day should be a cell Pac-Man eats; anything else means the layout changed
            print(f"::warning::{path.name}: matched {changed} cells to {active} active days, so it is published as the action drew it")
            continue
        path.write_text(svg, encoding="utf-8")
        print(f"re-shaded {changed} days in {path.name}")
