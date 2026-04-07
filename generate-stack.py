import base64
import json
import os
import urllib.request

USERNAME = "jeremy-prt"
DISPLAY_NAME = "Jérémy"
BIRTH_DATE = "2003-08-02"
MIN_PCT = 5.0

LANG_COLORS = {
    "Swift": "#F05138", "TypeScript": "#3178C6", "HTML": "#E34C26",
    "Vue": "#41B883", "Objective-C": "#438EFF", "JavaScript": "#F7DF1E",
    "Hack": "#878787", "CSS": "#563D7C", "PHP": "#4F5D95", "Twig": "#8DC63F",
    "C++": "#F34B7D", "Dart": "#00B4AB", "CMake": "#DA3434", "Shell": "#89E051",
    "C": "#555555", "Dockerfile": "#384D54", "Kotlin": "#A97BFF",
    "Python": "#3572A5", "Ruby": "#701516", "Go": "#00ADD8",
    "Rust": "#DEA584", "Java": "#B07219", "Lua": "#000080",
    "SCSS": "#C6538C", "Svelte": "#FF3E00",
}
DEFAULT_COLOR = "#8b949e"


def fetch(url):
    headers = {"User-Agent": "github-stack-gen"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        return r.read()


def fetch_json(url):
    return json.loads(fetch(url))


def to_b64(url):
    return base64.b64encode(fetch(url)).decode()


# Compute age
from datetime import date, datetime, timezone

birth = date.fromisoformat(BIRTH_DATE)
today = date.today()
age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

# Fetch images — avatar from repo (custom photo), banner from repo
avatar_b64 = to_b64(
    f"https://raw.githubusercontent.com/{USERNAME}/{USERNAME}/main/avatar.png"
)
banner_b64 = to_b64(
    f"https://raw.githubusercontent.com/{USERNAME}/{USERNAME}/main/banner.png"
)

# Fetch languages
repos = fetch_json(
    f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated"
)

lang_bytes = {}
total_commits = 0
for repo in repos:
    if repo.get("fork"):
        continue
    langs = fetch_json(repo["languages_url"])
    for lang, count in langs.items():
        lang_bytes[lang] = lang_bytes.get(lang, 0) + count

# Compute avg commits/year
user = fetch_json(f"https://api.github.com/users/{USERNAME}")
created = user.get("created_at", "2023-01-01T00:00:00Z")
created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
years = max(
    1, (datetime.now(timezone.utc) - created_dt).days / 365.25
)

non_fork_repos = [r for r in repos if not r.get("fork")]
total_commits = 0
for repo in non_fork_repos:
    try:
        contribs = fetch_json(
            f"https://api.github.com/repos/{USERNAME}/{repo['name']}/contributors"
        )
        for c in contribs:
            if c.get("login", "").lower() == USERNAME.lower():
                total_commits += c.get("contributions", 0)
    except Exception:
        pass

avg_commits = round(total_commits / years)

# Filter languages
total = sum(lang_bytes.values())
sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])
MAX_LANGS = 6
data = [
    (name, count / total * 100, LANG_COLORS.get(name, DEFAULT_COLOR))
    for name, count in sorted_langs
][:MAX_LANGS]

# SVG layout
WIDTH = 840
P = 28
R = 10
BANNER_H = 210
AVATAR_SIZE = 64
AVATAR_X = P
AVATAR_Y = BANNER_H - AVATAR_SIZE // 2
NAME_Y = AVATAR_Y + AVATAR_SIZE + 24
TITLE_Y = NAME_Y + 28
COLS = 2
COL_GAP = 32
COL_W = (WIDTH - P * 2 - COL_GAP) // COLS
ROW_H = 46
MAX_PCT = data[0][1] if data else 1
BAR_H = 6
GRID_Y = TITLE_Y + 24
ROWS = (len(data) + COLS - 1) // COLS
FOOTER_Y = GRID_Y + ROWS * ROW_H + 8
SVG_H = FOOTER_Y + 28

grid = ""
for i, (name, pct, color) in enumerate(data):
    col = i % COLS
    row = i // COLS
    lx = P + col * (COL_W + COL_GAP)
    ly = GRID_Y + row * ROW_H
    bar_fill = COL_W * (pct / MAX_PCT)
    grid += (
        f'<g transform="translate({lx},{ly})">\n'
        f'  <circle cx="6" cy="7" r="5" fill="{color}"/>\n'
        f'  <text x="18" y="11" class="lang">{name}</text>\n'
        f'  <text x="{COL_W}" y="11" class="pct" text-anchor="end">{pct:.1f}%</text>\n'
        f'  <rect x="0" y="20" width="{COL_W}" height="{BAR_H}" rx="3" fill="#21262d"/>\n'
        f'  <rect x="0" y="20" width="{bar_fill:.1f}" height="{BAR_H}" rx="3" fill="{color}"/>\n'
        f"</g>\n"
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{SVG_H}" viewBox="0 0 {WIDTH} {SVG_H}">
  <style>
    .bg {{ fill: #0d1117; }}
    .bd {{ fill: none; stroke: #30363d; stroke-width: 1; }}
    .name {{ fill: #e6edf3; font: 700 18px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; }}
    .section {{ fill: #8b949e; font: 400 14px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; }}
    .lang {{ fill: #e6edf3; font: 500 13px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; }}
    .pct {{ fill: #8b949e; font: 400 12px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; }}
    .footer {{ fill: #484f58; font: 400 11px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; }}
  </style>
  <defs>
    <clipPath id="banner-clip">
      <path d="M{R},0 H{WIDTH-R} Q{WIDTH},0 {WIDTH},{R} V{BANNER_H} H0 V{R} Q0,0 {R},0 Z"/>
    </clipPath>
    <clipPath id="avatar-clip">
      <circle cx="{AVATAR_X + AVATAR_SIZE//2}" cy="{AVATAR_Y + AVATAR_SIZE//2}" r="{AVATAR_SIZE//2}"/>
    </clipPath>
  </defs>

  <rect class="bg" width="{WIDTH}" height="{SVG_H}" rx="{R}"/>
  <rect class="bd" x=".5" y=".5" width="{WIDTH-1}" height="{SVG_H-1}" rx="{R}"/>

  <image x="0" y="0" width="{WIDTH}" height="{BANNER_H}" preserveAspectRatio="xMidYMid slice" clip-path="url(#banner-clip)" href="data:image/png;base64,{banner_b64}"/>

  <image x="{AVATAR_X}" y="{AVATAR_Y}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" clip-path="url(#avatar-clip)" href="data:image/png;base64,{avatar_b64}"/>
  <circle cx="{AVATAR_X + AVATAR_SIZE//2}" cy="{AVATAR_Y + AVATAR_SIZE//2}" r="{AVATAR_SIZE//2}" fill="none" stroke="#0d1117" stroke-width="3"/>

  <text x="{P}" y="{NAME_Y}" class="name">{DISPLAY_NAME} / {age} ans</text>
  <text x="{P}" y="{TITLE_Y}" class="section">Top {MAX_LANGS} most used languages</text>

  {grid}

  <text x="{WIDTH - P}" y="{FOOTER_Y + 14}" class="footer" text-anchor="end">~ {avg_commits} commits / year on average</text>
</svg>'''

with open("tech-stack.svg", "w") as f:
    f.write(svg)

print(f"Generated tech-stack.svg — {len(data)} languages, ~{avg_commits} commits/year")
