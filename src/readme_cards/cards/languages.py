"""Language breakdown by bytes, across public AND private repositories."""
from __future__ import annotations

from ..github import Stats
from ..render import Theme, bytes_human, frame, lang_color, text

W = 460
TOP, ROW = 96, 26
BAR_X, BAR_W = 150, 236


def render(s: Stats, theme: Theme, limit: int = 8, excluded: list[str] | None = None) -> str:
    items = list(s.languages.items())[:limit]
    if not items:
        p = frame(W, 120, theme, "Languages", "no language data visible to this token")
        p.append("</svg>")
        return "\n".join(p)

    total = sum(s.languages.values())
    height = TOP + ROW * len(items) + 18
    sub = f"{s.repositories} repositories, public and private · {bytes_human(total)}"
    p = frame(W, height, theme, "Languages by code volume", sub)
    if excluded:
        p.append(text(24, 70, f"excluding generated {', '.join(excluded)}",
                      fill=theme.muted, size=9.5, opacity=0.8))

    widest = items[0][1]
    for i, (lang, size) in enumerate(items):
        y = TOP + i * ROW
        color = lang_color(lang, i)
        fill_w = max(3.0, BAR_W * size / widest)
        p += [
            text(24, y + 11, lang, fill=theme.text, size=12),
            f'<rect x="{BAR_X}" y="{y+2}" width="{BAR_W}" height="11" rx="5.5" '
            f'fill="{theme.panel}"/>',
            f'<rect x="{BAR_X}" y="{y+2}" width="{fill_w:.1f}" height="11" rx="5.5" '
            f'fill="{color}"/>',
            text(W - 24, y + 11, f"{size/total*100:.1f}%", fill=theme.muted, size=11,
                 anchor="end"),
        ]
    p.append("</svg>")
    return "\n".join(p)
