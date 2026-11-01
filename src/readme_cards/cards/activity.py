"""Contribution activity over the last year, as a smoothed area chart."""
from __future__ import annotations

from datetime import date

from ..github import Stats
from ..render import Theme, frame, human, text

W, H = 820, 240
PAD_L, PAD_R, PAD_T, PAD_B = 48, 24, 78, 36
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _weekly(cal: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Collapse days into weeks so the line is readable at 820px."""
    out = []
    for i in range(0, len(cal), 7):
        chunk = cal[i:i + 7]
        out.append((chunk[0][0], sum(c for _, c in chunk)))
    return out


def render(s: Stats, theme: Theme) -> str:
    series = _weekly(s.calendar)
    if len(series) < 2:
        p = frame(W, 120, theme, "Contribution activity", "not enough data")
        p.append("</svg>")
        return "\n".join(p)

    peak = max(c for _, c in series) or 1
    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B
    step = plot_w / (len(series) - 1)

    def xy(i: int, count: int) -> tuple[float, float]:
        return PAD_L + i * step, PAD_T + plot_h - (count / peak) * plot_h

    pts = [xy(i, c) for i, (_, c) in enumerate(series)]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"
                    for i, (x, y) in enumerate(pts))
    area = (f"{line} L{pts[-1][0]:.1f},{PAD_T+plot_h} "
            f"L{pts[0][0]:.1f},{PAD_T+plot_h} Z")

    sub = (f"{human(s.total_contributions)} contributions · "
           f"{s.active_days} active days · peak {peak} in a week")
    p = frame(W, H, theme, "Contribution activity", sub)
    p.append(f'<defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0%" stop-color="{theme.accent}" stop-opacity="0.38"/>'
             f'<stop offset="100%" stop-color="{theme.accent}" stop-opacity="0.02"/>'
             f'</linearGradient></defs>')

    # horizontal guides + y labels
    for frac in (0, 0.5, 1.0):
        y = PAD_T + plot_h - frac * plot_h
        p.append(f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W-PAD_R}" y2="{y:.1f}" '
                 f'stroke="{theme.border}" stroke-width="1" opacity="0.55"/>')
        p.append(text(PAD_L - 10, y + 4, human(int(peak * frac)), fill=theme.muted,
                      size=10, anchor="end"))

    p.append(f'<path d="{area}" fill="url(#fade)"/>')
    p.append(f'<path d="{line}" fill="none" stroke="{theme.accent}" stroke-width="2" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')

    # month ticks, one label per month change
    seen = None
    for i, (iso, _) in enumerate(series):
        m = date.fromisoformat(iso).month
        if m != seen:
            seen = m
            x = PAD_L + i * step
            p.append(text(x, H - 14, MONTHS[m - 1], fill=theme.muted, size=10,
                          anchor="middle"))

    # mark the peak week
    pi = max(range(len(series)), key=lambda i: series[i][1])
    px, py = pts[pi]
    p.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{theme.accent}" '
             f'stroke="{theme.bg}" stroke-width="2"/>')
    p.append("</svg>")
    return "\n".join(p)
