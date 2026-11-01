"""Overview card: contributions, commits, PRs, reviews and streaks."""
from __future__ import annotations

from ..github import Stats
from ..render import Theme, frame, human, text

W, H = 460, 200


def render(s: Stats, theme: Theme) -> str:
    current, longest = s.streaks()
    sub = f"last 12 months · {s.active_days} active days"
    if s.restricted:
        sub += f" · {human(s.restricted)} private hidden"
    p = frame(W, H, theme, f"{s.name} — GitHub activity", sub)

    rows = [
        ("Contributions", s.total_contributions),
        ("Commits", s.commits),
        ("Pull requests", s.pull_requests),
        ("Reviews", s.reviews),
    ]
    for i, (label, value) in enumerate(rows):
        y = 84 + i * 24
        p.append(text(24, y, label, fill=theme.muted, size=12))
        p.append(text(232, y, human(value), fill=theme.text, size=12, weight=600,
                      anchor="end"))

    # streak dial
    cx, cy, r = 352, 112, 44
    circ = 2 * 3.14159 * r
    pct = 0.0 if longest == 0 else min(1.0, current / longest)
    p += [
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{theme.panel}" '
        f'stroke-width="8"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{theme.accent}" '
        f'stroke-width="8" stroke-linecap="round" '
        f'stroke-dasharray="{circ*pct:.1f} {circ:.1f}" '
        f'transform="rotate(-90 {cx} {cy})"/>',
        text(cx, cy + 2, current, fill=theme.text, size=26, weight=700, anchor="middle"),
        text(cx, cy + 20, "day streak", fill=theme.muted, size=10, anchor="middle"),
        text(cx, cy + 68, f"longest {longest}", fill=theme.muted, size=10,
             anchor="middle"),
    ]
    p.append("</svg>")
    return "\n".join(p)
