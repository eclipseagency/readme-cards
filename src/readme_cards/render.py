"""SVG building blocks and themes. No dependencies."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape

FONT = ("ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',"
        "Ubuntu,Helvetica,Arial,sans-serif")


@dataclass(frozen=True)
class Theme:
    bg: str
    panel: str
    border: str
    text: str
    muted: str
    accent: str


THEMES = {
    "dark":     Theme("#0d1117", "#161b22", "#30363d", "#e6edf3", "#8b949e", "#f59e0b"),
    "light":    Theme("#ffffff", "#f6f8fa", "#d0d7de", "#1f2328", "#59636e", "#bc4c00"),
    "gruvbox":  Theme("#1d2021", "#282828", "#3c3836", "#ebdbb2", "#a89984", "#fabd2f"),
    "dracula":  Theme("#282a36", "#343746", "#44475a", "#f8f8f2", "#6272a4", "#bd93f9"),
    "nord":     Theme("#2e3440", "#3b4252", "#434c5e", "#eceff4", "#8d98af", "#88c0d0"),
    "midnight": Theme("#0b0e14", "#141922", "#242b38", "#e6e6e6", "#8a94a7", "#4dabf7"),
}

# GitHub's own language colours for the ones that actually show up.
LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572a5",
    "Go": "#00add8", "Rust": "#dea584", "Java": "#b07219", "C#": "#178600",
    "C++": "#f34b7d", "C": "#555555", "PHP": "#4f5d95", "Ruby": "#701516",
    "Swift": "#f05138", "Kotlin": "#a97bff", "Dart": "#00b4ab",
    "HTML": "#e34c26", "CSS": "#563d7c", "SCSS": "#c6538c", "Vue": "#41b883",
    "Shell": "#89e051", "PowerShell": "#012456", "Lua": "#000080",
    "PLpgSQL": "#336790", "TSQL": "#e38c00", "Blade": "#f7523f",
    "Svelte": "#ff3e00", "Astro": "#ff5a03", "Elixir": "#6e4a7e",
    "Haskell": "#5e5086", "Scala": "#c22d40", "Zig": "#ec915c",
    "Jupyter Notebook": "#da5b0b", "Dockerfile": "#384d54", "Nix": "#7e7eff",
}
FALLBACK_COLORS = ["#f59e0b", "#3fb950", "#58a6ff", "#db61a2", "#a371f7",
                   "#ff7b72", "#79c0ff", "#d29922"]


def lang_color(name: str, index: int) -> str:
    return LANG_COLORS.get(name, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def human(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 10_000:
        return f"{n/1000:.0f}k"
    if n >= 1_000:
        return f"{n/1000:.1f}k".replace(".0k", "k")
    return str(n)


def bytes_human(n: int) -> str:
    for unit, div in (("GB", 1 << 30), ("MB", 1 << 20), ("kB", 1 << 10)):
        if n >= div:
            return f"{n/div:.1f} {unit}"
    return f"{n} B"


def text(x, y, body, *, fill, size=13, weight=400, anchor="start", opacity=None):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{op}>{escape(str(body))}</text>')


def frame(width: int, height: int, theme: Theme, title: str, subtitle: str = "") -> list[str]:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" '
        f'font-family="{FONT}">',
        f'<rect width="{width}" height="{height}" rx="12" fill="{theme.bg}" '
        f'stroke="{theme.border}"/>',
        text(24, 34, title, fill=theme.accent, size=15, weight=600),
    ]
    if subtitle:
        parts.append(text(24, 53, subtitle, fill=theme.muted, size=11))
    return parts
