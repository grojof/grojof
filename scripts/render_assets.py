#!/usr/bin/env python3
"""Render the profile's images: header, project cards and stack, in light and dark.

    python3 scripts/render_assets.py

Standard library only. Logos come from Simple Icons (CC0), pinned below and cached
in ``.cache/``. Edit the texts and colours here and run it again; never edit the
SVGs by hand.
"""

from __future__ import annotations

import json
import re
import zlib
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CACHE = ROOT / ".cache"
SIMPLE_ICONS = "16.34.0"

THEMES = {
    "dark": dict(bg="#14111A", panel="#1D1824", stroke="#2E2634", fg="#EDE6EE", muted="#A99BAA",
                 plum="#C08AB4", amber="#E8B04B", ok="#7BC59A"),
    "light": dict(bg="#FBF8FA", panel="#F2ECF1", stroke="#E3DAE2", fg="#241C26", muted="#6B5D6A",
                  plum="#714B67", amber="#C98A12", ok="#2F8A57"),
}

SANS = '-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif'
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace'
REDUCED = "@media (prefers-reduced-motion:reduce){{{sel}{{animation:none!important;opacity:1!important}}}}"


# --- shared -----------------------------------------------------------------------

def frame(width: int, height: int, label: str, style: str, body: str, t: dict) -> str:
    # A clip id of its own: several of these inlined in one page must not share one.
    clip = f"c{zlib.crc32((label + t['bg']).encode()):08x}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">
<style>
.sans{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
{style}
</style>
<defs><clipPath id="{clip}"><rect width="{width}" height="{height}" rx="18"/></clipPath></defs>
<g clip-path="url(#{clip})">
<rect width="{width}" height="{height}" fill="{t['bg']}"/>
<rect width="{width}" height="5" fill="{t['plum']}"/>
<rect width="{width // 3}" height="5" fill="{t['amber']}"/>
{body}
</g>
</svg>
"""


def write(name: str, svg: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(svg, encoding="utf-8")


# --- header -------------------------------------------------------------------------

HEADER_ROWS = [
    ("spec", "agreed before the first line of code"),
    ("build", "small steps, previewed, reversible"),
    ("verify", "run against the real thing"),
    ("document", "the docs move with the code"),
]


def header(t: dict) -> str:
    cycle, slot = 8.0, 2.0
    rows = []
    for i, (word, text) in enumerate(HEADER_ROWS):
        y = 178 + i * 28
        delay = f"animation-delay:{i * slot:.1f}s"
        rows.append(
            f'<text x="60" y="{y}" class="mono kw" fill="{t["plum"]}">{word}</text>'
            f'<text x="60" y="{y}" class="mono kw on" fill="{t["amber"]}" style="{delay}">{word}</text>'
            f'<text x="170" y="{y}" class="mono txt" fill="{t["fg"]}" style="{delay}">{escape(text)}</text>'
        )
        if word == "verify":
            rows.append(f'<text x="430" y="{y}" class="mono kw on" fill="{t["ok"]}" style="{delay}">✓</text>')
    style = (
        f".kw{{font-size:15px;font-weight:700}}.txt{{font-size:15px;opacity:.45;animation:lit {cycle}s infinite}}"
        f".on{{opacity:0;animation:lit {cycle}s infinite}}"
        "@keyframes lit{0%{opacity:.45}4%{opacity:1}24%{opacity:1}28%{opacity:.45}100%{opacity:.45}}"
        ".on{animation-name:on}@keyframes on{0%{opacity:0}4%{opacity:1}24%{opacity:1}28%{opacity:0}100%{opacity:0}}"
        + REDUCED.format(sel=".txt,.on")
    )
    body = (
        f'<text x="56" y="76" class="sans" font-size="40" font-weight="700" fill="{t["fg"]}">Guillermo Rojo</text>'
        f'<text x="56" y="108" class="sans" font-size="18" fill="{t["muted"]}">'
        "Senior Odoo Engineer · Full-Stack Developer · systems that run in production</text>"
        f'<line x1="56" y1="132" x2="844" y2="132" stroke="{t["stroke"]}"/>'
        f'<rect x="40" y="148" width="820" height="128" rx="12" fill="{t["panel"]}"/>' + "".join(rows)
    )
    label = "Guillermo Rojo — Senior Odoo Engineer · Full-Stack Developer. " + "; ".join(
        f"{w}: {x}" for w, x in HEADER_ROWS)
    return frame(900, 300, label, style, body, t)


# --- project cards ------------------------------------------------------------------

def chips(x: int, y: int, names: list[str], t: dict) -> str:
    out, cx = [], x
    for name in names:
        w = 16 + 7.2 * len(name)
        out.append(f'<rect x="{cx}" y="{y}" width="{w:.0f}" height="24" rx="12" fill="none" stroke="{t["stroke"]}"/>'
                   f'<text x="{cx + w / 2:.0f}" y="{y + 16}" class="sans" font-size="12" text-anchor="middle" '
                   f'fill="{t["muted"]}">{escape(name)}</text>')
        cx += w + 8
    return "".join(out)


def card(title: str, lines: list[str], tags: list[str], art: str, style: str, t: dict) -> str:
    text = "".join(
        f'<text x="40" y="{82 + i * 22}" class="sans" font-size="15" fill="{t["muted"]}">{escape(line)}</text>'
        for i, line in enumerate(lines))
    body = (
        f'<text x="40" y="54" class="sans" font-size="24" font-weight="700" fill="{t["fg"]}">{escape(title)}</text>'
        f'{text}{chips(40, 132, tags, t)}'
        f'<rect x="560" y="22" width="316" height="146" rx="12" fill="{t["panel"]}"/>{art}'
    )
    return frame(900, 190, f"{title} — {' '.join(lines)}", style, body, t)


def card_dwg(t: dict) -> str:
    majors = list(range(12, 19))
    pills, x0 = [], 578
    for i, major in enumerate(majors):
        x = x0 + i * 41
        color = t["amber"] if major == 18 else t["plum"]
        pills.append(f'<g class="step" style="animation-delay:{0.4 + i * 0.4:.1f}s">'
                     f'<rect x="{x}" y="70" width="35" height="30" rx="8" fill="{color}"/>'
                     f'<text x="{x + 17.5}" y="90" class="mono" font-size="13" font-weight="700" '
                     f'text-anchor="middle" fill="{t["bg"]}">{major}</text></g>')
    art = ("".join(pills)
           + f'<text x="718" y="134" class="mono done" font-size="13" text-anchor="middle" fill="{t["ok"]}">'
           "12.0 → 18.0  ✓</text>")
    style = (".step{opacity:.18;animation:step 9s infinite}"
             "@keyframes step{0%{opacity:.18}4%{opacity:1}70%{opacity:1}80%{opacity:.18}100%{opacity:.18}}"
             ".done{opacity:0;animation:done 9s infinite;animation-delay:3.2s}"
             "@keyframes done{0%{opacity:0}4%{opacity:1}40%{opacity:1}48%{opacity:0}100%{opacity:0}}"
             + REDUCED.format(sel=".step,.done"))
    return card("odoo_dwg", ["Odoo development workspaces and OpenUpgrade", "migrations from 12.0 to 19.0, on any Linux host."],
                ["Python", "standard library only", "OpenUpgrade"], art, style, t)


def card_im(t: dict) -> str:
    sites = [("erp", "18.0"), ("shop", "17.0"), ("test", "16.0")]
    rows = []
    for i, (name, version) in enumerate(sites):
        y = 44 + i * 40
        rows.append(f'<rect x="590" y="{y}" width="256" height="30" rx="8" fill="{t["bg"]}" stroke="{t["stroke"]}"/>'
                    f'<circle cx="610" cy="{y + 15}" r="5" fill="{t["ok"]}" class="dot" '
                    f'style="animation-delay:{i * 0.6:.1f}s"/>'
                    f'<text x="626" y="{y + 20}" class="mono" font-size="13" fill="{t["fg"]}">{name}</text>'
                    f'<text x="834" y="{y + 20}" class="mono" font-size="13" text-anchor="end" '
                    f'fill="{t["muted"]}">odoo {version}</text>')
    style = (".dot{animation:pulse 2.4s ease-in-out infinite}"
             "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}" + REDUCED.format(sel=".dot"))
    return card("odoo_instance_manager", ["Several Odoo sites on one Ubuntu server, from one", "menu: installs, copies, backups, nginx, fail2ban."],
                ["Python", "Ubuntu", "operations"], "".join(rows), style, t)


def card_eunomai(t: dict) -> str:
    pillars = [("specs", 70), ("docs", 92), ("controls", 58), ("skills", 80)]
    bars = []
    for i, (name, height) in enumerate(pillars):
        x = 592 + i * 66
        bars.append(f'<rect x="{x}" y="{142 - height}" width="50" height="{height}" rx="8" '
                    f'fill="{t["amber"] if i == 1 else t["plum"]}" class="bar" style="animation-delay:{i * 0.25:.2f}s"/>'
                    f'<text x="{x + 25}" y="160" class="sans" font-size="12" text-anchor="middle" '
                    f'fill="{t["muted"]}">{name}</text>')
    style = (".bar{transform-box:fill-box;transform-origin:bottom;animation:grow 1s ease-out both}"
             "@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}" + REDUCED.format(sel=".bar"))
    return card("eunomai", ["A focused, Claude-only AI workspace as a Claude Code", "plugin: specs, living docs, safe controls, skills."],
                ["TypeScript", "Claude Code", "spec-driven"], "".join(bars), style, t)


# --- stack --------------------------------------------------------------------------

STACK = [
    ("Core & ERP", [("odoo", "Odoo"), ("python", "Python"), ("postgresql", "PostgreSQL"),
                    (None, "Business Central", "BC")]),
    ("Web & apps", [("typescript", "TypeScript"), ("react", "React"), ("nodedotjs", "Node.js"),
                    ("flutter", "Flutter"), ("dart", "Dart")]),
    ("Systems & DevOps", [("linux", "Linux"), (None, "WSL 2", "WSL"), (None, "Windows", "Win"),
                          (None, "PowerShell", "PS"), ("gnubash", "Bash"), ("docker", "Docker"),
                          ("nginx", "nginx"), ("git", "Git"), ("githubactions", "GitHub Actions")]),
    ("AI tooling", [("claude", "Claude"), ("claude", "Claude Code"), ("githubcopilot", "GitHub Copilot")]),
]
ALSO = [("dotnet", "C# / .NET"), ("angular", "Angular"), ("ionic", "Ionic"), ("django", "Django"),
        ("supabase", "Supabase")]


def simple_icon(slug: str) -> tuple[str, str]:
    """``(path, hex)`` of a Simple Icons logo, fetched once into the cache."""
    CACHE.mkdir(exist_ok=True)
    base = f"https://cdn.jsdelivr.net/npm/simple-icons@{SIMPLE_ICONS}"
    data_file = CACHE / f"simple-icons-{SIMPLE_ICONS}.json"
    if not data_file.exists():
        data_file.write_bytes(urllib.request.urlopen(f"{base}/data/simple-icons.json").read())
    svg_file = CACHE / f"{slug}.svg"
    if not svg_file.exists():
        svg_file.write_bytes(urllib.request.urlopen(f"{base}/icons/{slug}.svg").read())
    hexc = next(d["hex"] for d in json.loads(data_file.read_text()) if d["slug"] == slug)
    match = re.search(r'<path d="([^"]+)"', svg_file.read_text())
    if match is None:
        raise ValueError(f"no path in {svg_file}")
    return match.group(1), hexc


def _lum(hexc: str) -> float:
    def f(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def readable(hexc: str, t: dict) -> str:
    """The brand colour, unless it disappears on this theme's tile."""
    for back in (t["bg"], t["panel"]):
        hi, lo = sorted((_lum(hexc), _lum(back.lstrip("#"))), reverse=True)
        if (hi + 0.05) / (lo + 0.05) < 2.2:
            return t["fg"]
    return "#" + hexc


def tile(x: float, y: float, w: float, h: float, item: tuple, delay: float, t: dict, small=False) -> str:
    slug, name = item[0], item[1]
    size, pad = (14, 10) if small else (18, 12)
    iy = y + (h - size) / 2
    parts = [f'<g class="tile" style="animation-delay:{delay:.2f}s">',
             f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 4:.0f}" fill="{t["panel"]}" stroke="{t["stroke"]}"/>']
    text_x = x + pad + size + 10
    if slug == "odoo":  # a wordmark: wider, or it cannot be read
        path, hexc = simple_icon(slug)
        parts.append(f'<g transform="translate({x + pad - 2},{iy - 9}) scale(1.5)"><path d="{path}" fill="{readable(hexc, t)}"/></g>')
        text_x = x + pad + 46
    elif slug:
        path, hexc = simple_icon(slug)
        parts.append(f'<g transform="translate({x + pad},{iy}) scale({size / 24})"><path d="{path}" fill="{readable(hexc, t)}"/></g>')
    else:
        letters = item[2]
        parts.append(f'<rect x="{x + pad}" y="{iy}" width="{size}" height="{size}" rx="4" fill="{t["plum"]}"/>'
                     f'<text x="{x + pad + size / 2}" y="{iy + size * 0.68:.1f}" class="mono" text-anchor="middle" '
                     f'font-size="{9 if len(letters) < 3 else 7.5}" font-weight="700" fill="{t["bg"]}">{letters}</text>')
    parts.append(f'<text x="{text_x}" y="{y + h / 2 + 5:.1f}" class="sans" font-size="{13 if small else 14}" '
                 f'font-weight="{500 if small else 600}" fill="{t["fg"] if not small else t["muted"]}">{escape(name)}</text></g>')
    return "".join(parts)


def stack(t: dict) -> str:
    width, padx, label_w, tw, th, gap, per_row = 900, 40, 170, 152, 40, 10, 4
    y, n, parts = 34, 0, []
    for label, items in STACK:
        parts.append(f'<text x="{padx}" y="{y + 25}" class="sans lab" fill="{t["plum"]}">{escape(label.upper())}</text>')
        for i, item in enumerate(items):
            x = padx + label_w + (i % per_row) * (tw + gap)
            parts.append(tile(x, y + (i // per_row) * (th + gap), tw, th, item, 0.15 + n * 0.04, t))
            n += 1
        y += ((len(items) + per_row - 1) // per_row) * (th + gap) + 22
        parts.append(f'<line x1="{padx}" y1="{y - 12}" x2="{width - padx}" y2="{y - 12}" stroke="{t["stroke"]}"/>')
    parts.append(f'<text x="{padx}" y="{y + 20}" class="sans lab" fill="{t["muted"]}">ALSO WORKED WITH</text>')
    sw, sh = 120, 32
    for i, item in enumerate(ALSO):
        parts.append(tile(padx + label_w + i * (sw + 8), y, sw, sh, item, 0.15 + n * 0.04, t, small=True))
        n += 1
    height = y + sh + 26
    style = (".lab{font-size:12px;font-weight:700;letter-spacing:.12em}"
             ".tile{opacity:0;animation:rise .5s ease-out forwards}"
             "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
             + REDUCED.format(sel=".tile"))
    label = "Stack. " + " ".join(f"{g}: {', '.join(i[1] for i in its)}." for g, its in STACK) + \
        " Also worked with: " + ", ".join(i[1] for i in ALSO) + "."
    return frame(width, height, label, style, "".join(parts), t)


def main() -> None:
    for theme, t in THEMES.items():
        write(f"header-{theme}.svg", header(t))
        write(f"card-dwg-{theme}.svg", card_dwg(t))
        write(f"card-im-{theme}.svg", card_im(t))
        write(f"card-eunomai-{theme}.svg", card_eunomai(t))
        write(f"stack-{theme}.svg", stack(t))
    print("rendered", ", ".join(sorted(p.name for p in ASSETS.glob("*.svg"))))


if __name__ == "__main__":
    main()
