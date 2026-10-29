"""Fetch a GitLab user's contribution calendar and render it as a dark, neon SVG."""
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

USER = os.environ.get("GITLAB_USER", "").strip()
HOST = os.environ.get("GITLAB_HOST", "https://gitlab.com").rstrip("/")
OUT = os.environ.get("OUT", "assets/gitlab-contributions.svg")

if not USER or USER == "EDIT":
    sys.exit("Set GITLAB_USER to your GitLab username.")

req = urllib.request.Request(
    f"{HOST}/users/{USER}/calendar.json",
    headers={"Accept": "application/json", "User-Agent": "contrib-graph"},
)
with urllib.request.urlopen(req, timeout=30) as r:
    data = {k: int(v) for k, v in json.load(r).items()}

today = date.today()
start = today - timedelta(days=364)
start -= timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday

colors = ["#161b22", "#0a3d2e", "#0f7a5a", "#00c98d", "#00ffb2"]
nonzero = sorted(v for v in data.values() if v > 0)


def level(n):
    if n <= 0 or not nonzero:
        return 0
    q = lambda p: nonzero[min(len(nonzero) - 1, int(len(nonzero) * p))]
    if n <= q(0.25):
        return 1
    if n <= q(0.5):
        return 2
    if n <= q(0.75):
        return 3
    return 4


CELL, GAP, LEFT, TOP = 11, 3, 16, 38
weeks = ((today - start).days // 7) + 1
width = LEFT + weeks * (CELL + GAP) + 16
height = TOP + 7 * (CELL + GAP) + 18

total = sum(v for k, v in data.items() if start.isoformat() <= k <= today.isoformat())
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="JetBrains Mono, monospace">',
    f'<rect width="{width}" height="{height}" rx="10" fill="#0d1117"/>',
    f'<text x="{LEFT}" y="22" fill="#00ffb2" font-size="12" font-weight="600">gitlab / {USER} - {total} contributions in the last year</text>',
]

last_month = None
for w in range(weeks):
    for d in range(7):
        day = start + timedelta(days=w * 7 + d)
        if day > today:
            continue
        x = LEFT + w * (CELL + GAP)
        y = TOP + d * (CELL + GAP)
        n = data.get(day.isoformat(), 0)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{colors[level(n)]}"><title>{day.isoformat()}: {n}</title></rect>'
        )
        if d == 0 and day.month != last_month:
            last_month = day.month
            parts.append(f'<text x="{x}" y="{TOP - 6}" fill="#7d8590" font-size="9">{day.strftime("%b")}</text>')

parts.append("</svg>")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write("\n".join(parts))
print(f"wrote {OUT} ({total} contributions)")
