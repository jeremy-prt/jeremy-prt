import base64
import json
import os
import urllib.request
from datetime import date, datetime, timezone

USERNAME = "jeremy-prt"
DISPLAY_NAME = "Jérémy"
BIRTH_DATE = "2003-08-02"
MAX_LANGS = 6

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

DAILY_COLORS = [
    "#c084fc", "#60a5fa", "#34d399", "#f472b6",
    "#fb923c", "#a78bfa", "#38bdf8",
]

GHOST_PHRASES = [
    "hello", "boo~", "*stares*", "&lt; / &gt;", "git push", "zzZ",
    "npm install", "404", "*floats*", "debug me", "void(0)",
    "sudo rm -rf", "*lurks*", "ping?", "EOF", "null",
]
PHRASE_TIMES = [2, 6.5, 9, 14, 18.5, 23, 26, 31, 35.5, 39, 43, 47.5, 50, 53, 56, 59]
PHRASE_CYCLE = 60


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


# Daily color
today = date.today()
COLOR = DAILY_COLORS[today.timetuple().tm_yday % len(DAILY_COLORS)]

# Age
birth = date.fromisoformat(BIRTH_DATE)
age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

# Images
avatar_b64 = to_b64(
    f"https://raw.githubusercontent.com/{USERNAME}/{USERNAME}/main/avatar.png"
)
banner_b64 = to_b64(
    f"https://raw.githubusercontent.com/{USERNAME}/{USERNAME}/main/banner.png"
)

# Languages
repos = fetch_json(
    f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated"
)

lang_bytes = {}
for repo in repos:
    if repo.get("fork"):
        continue
    langs = fetch_json(repo["languages_url"])
    for lang, count in langs.items():
        lang_bytes[lang] = lang_bytes.get(lang, 0) + count

# Commits
user = fetch_json(f"https://api.github.com/users/{USERNAME}")
created = user.get("created_at", "2023-01-01T00:00:00Z")
created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
years = max(1, (datetime.now(timezone.utc) - created_dt).days / 365.25)

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
ACX = AVATAR_X + AVATAR_SIZE // 2
ACY = AVATAR_Y + AVATAR_SIZE // 2
RING_R = AVATAR_SIZE // 2 + 4
NAME_Y = AVATAR_Y + AVATAR_SIZE + 34
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

ring_circ = 2 * 3.14159 * RING_R
dash = ring_circ * 0.75

# Language grid
grid = ""
for i, (name, pct, color) in enumerate(data):
    col = i % COLS
    row = i // COLS
    lx = P + col * (COL_W + COL_GAP)
    ly = GRID_Y + row * ROW_H
    bar_fill = COL_W * (pct / MAX_PCT)
    delay = 0.5 + i * 0.15
    grid += (
        f'<g transform="translate({lx},{ly})" opacity="0">\n'
        f'  <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{delay}s" fill="freeze"/>\n'
        f'  <circle cx="6" cy="7" r="5" fill="{color}"/>\n'
        f'  <text x="18" y="11" class="lang">{name}</text>\n'
        f'  <text x="{COL_W}" y="11" class="pct" text-anchor="end">{pct:.1f}%</text>\n'
        f'  <rect x="0" y="20" width="{COL_W}" height="{BAR_H}" rx="3" fill="#21262d"/>\n'
        f'  <rect x="0" y="20" width="0" height="{BAR_H}" rx="3" fill="{color}">\n'
        f'    <animate attributeName="width" from="0" to="{bar_fill:.1f}" dur="0.8s" begin="{delay + 0.2}s" fill="freeze"/>\n'
        f"  </rect>\n"
        f"</g>\n"
    )

# Ghost phrases
phrase_svgs = ""
for i, phrase in enumerate(GHOST_PHRASES):
    begin = PHRASE_TIMES[i]
    show_end = begin + 2
    fade_out = show_end + 0.4
    t_start = begin / PHRASE_CYCLE
    t_show = (begin + 0.3) / PHRASE_CYCLE
    t_hide = show_end / PHRASE_CYCLE
    t_gone = min(fade_out / PHRASE_CYCLE, 0.999)
    phrase_svgs += (
        f'<text x="70" y="104" text-anchor="middle" fill="{COLOR}" '
        f'font-size="10" font-family="Courier New,monospace" opacity="0">'
        f'{phrase}<animate attributeName="opacity" '
        f'values="0;0;1;1;0;0" keyTimes="0;{t_start:.4f};{t_show:.4f};'
        f'{t_hide:.4f};{t_gone:.4f};1" dur="{PHRASE_CYCLE}s" '
        f'repeatCount="indefinite"/></text>\n'
    )

# Ghost buddy template
def ghost_frame(eyes, waves):
    return (
        f'<text x="34" y="16" fill="{COLOR}" font-size="12" '
        f'font-family="Courier New,monospace" xml:space="preserve">'
        f' ✦  ~^~  ✦</text>\n'
        f'<text x="34" y="30" fill="{COLOR}" font-size="12" '
        f'font-family="Courier New,monospace" xml:space="preserve">'
        f' .-------.</text>\n'
        f'<text x="34" y="44" fill="{COLOR}" font-size="12" '
        f'font-family="Courier New,monospace" xml:space="preserve">'
        f'|  {eyes}   {eyes}  |</text>\n'
        f'<text x="34" y="58" fill="{COLOR}" font-size="12" '
        f'font-family="Courier New,monospace" xml:space="preserve">'
        f'|   ~~~   |</text>\n'
        f'<text x="34" y="72" fill="{COLOR}" font-size="12" '
        f'font-family="Courier New,monospace" xml:space="preserve">'
        f'|         |</text>\n'
        f'<text x="34" y="86" fill="{COLOR}" font-size="12" '
        f'font-family="Courier New,monospace" xml:space="preserve">'
        f' {waves}</text>\n'
    )

GHOST_X = 640
GHOST_Y = 185

ghost_svg = f'''<g transform="translate({GHOST_X},{GHOST_Y}) scale(0.85)">
  <text x="8" y="30" fill="{COLOR}" font-size="9" opacity="0">✦<animate attributeName="opacity" values="0;0.8;0" dur="2.8s" repeatCount="indefinite"/></text>
  <text x="165" y="50" fill="{COLOR}" font-size="7" opacity="0">✦<animate attributeName="opacity" values="0;0.7;0" dur="3.2s" begin="1s" repeatCount="indefinite"/></text>
  <text x="12" y="80" fill="{COLOR}" font-size="6" opacity="0">✦<animate attributeName="opacity" values="0;0.9;0" dur="3.6s" begin="2s" repeatCount="indefinite"/></text>
  <text x="162" y="25" fill="{COLOR}" font-size="8" opacity="0">✦<animate attributeName="opacity" values="0;0.8;0" dur="2.5s" begin="0.6s" repeatCount="indefinite"/></text>
  <text x="155" y="85" fill="{COLOR}" font-size="7" opacity="0">✦<animate attributeName="opacity" values="0;0.7;0" dur="3s" begin="1.5s" repeatCount="indefinite"/></text>
  <g>
    <animateTransform attributeName="transform" type="translate" values="0,0;0,-3;0,0" dur="2s" repeatCount="indefinite"/>
    <g><animate attributeName="visibility" values="visible;hidden;hidden" dur="1.5s" repeatCount="indefinite"/>
      {ghost_frame("×", "~-~ ~-~ ~")}
    </g>
    <g visibility="hidden"><animate attributeName="visibility" values="hidden;visible;hidden" dur="1.5s" repeatCount="indefinite"/>
      {ghost_frame("×", "-~- -~- -")}
    </g>
    <g visibility="hidden"><animate attributeName="visibility" values="hidden;hidden;visible" dur="1.5s" repeatCount="indefinite"/>
      {ghost_frame("-", "~-- ~-- ~")}
    </g>
  </g>
  {phrase_svgs}
</g>'''

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
      <circle cx="{ACX}" cy="{ACY}" r="{AVATAR_SIZE//2}"/>
    </clipPath>
  </defs>

  <rect class="bg" width="{WIDTH}" height="{SVG_H}" rx="{R}"/>
  <rect class="bd" x=".5" y=".5" width="{WIDTH-1}" height="{SVG_H-1}" rx="{R}"/>

  <image x="0" y="0" width="{WIDTH}" height="{BANNER_H}" preserveAspectRatio="xMidYMid slice" clip-path="url(#banner-clip)" href="data:image/png;base64,{banner_b64}"/>

  <circle cx="{ACX}" cy="{ACY}" r="{RING_R}" fill="none" stroke="{COLOR}" stroke-width="2.5" stroke-dasharray="{dash:.1f} {ring_circ - dash:.1f}" stroke-linecap="round" opacity="0.9">
    <animateTransform attributeName="transform" type="rotate" from="0 {ACX} {ACY}" to="360 {ACX} {ACY}" dur="4.5s" repeatCount="indefinite"/>
  </circle>

  <image x="{AVATAR_X}" y="{AVATAR_Y}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" clip-path="url(#avatar-clip)" href="data:image/png;base64,{avatar_b64}"/>
  <circle cx="{ACX}" cy="{ACY}" r="{AVATAR_SIZE//2}" fill="none" stroke="#0d1117" stroke-width="3"/>

  <text x="{P}" y="{NAME_Y}" class="name" opacity="0">{DISPLAY_NAME} / {age} yo<animate attributeName="opacity" from="0" to="1" dur="0.6s" begin="0.1s" fill="freeze"/></text>

  <text x="{P}" y="{TITLE_Y}" class="section" opacity="0">Top {MAX_LANGS} most used languages<animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.4s" fill="freeze"/></text>

  {grid}

  <text x="{WIDTH - P}" y="{FOOTER_Y + 14}" class="footer" text-anchor="end" opacity="0">~ {avg_commits} commits / year on average<animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="1.8s" fill="freeze"/></text>

  {ghost_svg}
</svg>'''

with open("tech-stack.svg", "w") as f:
    f.write(svg)

print(f"Generated tech-stack.svg — {len(data)} languages, ~{avg_commits} commits/year, color: {COLOR}")
