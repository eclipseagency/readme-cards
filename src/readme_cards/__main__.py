"""readme-cards — generate GitHub profile cards into your own repository.

  python -m readme_cards --user octocat --cards stats,languages,activity

Requires GITHUB_TOKEN in the environment. Writes SVGs to --out (default: cards/).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

from .cards import RENDERERS
from .github import Client, GitHubError
from .render import THEMES

DEFAULT_EXCLUDE = "HTML,CSS"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="readme-cards",
        description="Generate GitHub profile stat cards as SVGs in your own repo.")
    ap.add_argument("--user", required=True, help="GitHub login to render")
    ap.add_argument("--cards", default="stats,languages,activity",
                    help=f"comma separated: {', '.join(RENDERERS)}")
    ap.add_argument("--theme", default="dark", choices=sorted(THEMES))
    ap.add_argument("--accent", default="", help="hex override, e.g. #f59e0b")
    ap.add_argument("--out", default="cards", help="output directory")
    ap.add_argument("--exclude-languages", default=DEFAULT_EXCLUDE,
                    help="languages to drop; build output such as HTML and CSS "
                         "otherwise dominates by bytes and misrepresents you. "
                         "Pass an empty string to keep everything.")
    ap.add_argument("--language-limit", type=int, default=8)
    ap.add_argument("--badge", action="store_true",
                    help="also write contributions.json, a shields.io endpoint")
    ap.add_argument("--token", default="", help="defaults to $GITHUB_TOKEN")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    token = args.token or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("error: set GITHUB_TOKEN, or pass --token", file=sys.stderr)
        return 2

    theme = THEMES[args.theme]
    if args.accent:
        accent = args.accent if args.accent.startswith("#") else f"#{args.accent}"
        theme = type(theme)(theme.bg, theme.panel, theme.border, theme.text,
                            theme.muted, accent)

    excluded = [x.strip() for x in args.exclude_languages.split(",") if x.strip()]
    wanted = [c.strip() for c in args.cards.split(",") if c.strip()]
    unknown = [c for c in wanted if c not in RENDERERS]
    if unknown:
        print(f"error: unknown card(s): {', '.join(unknown)}. "
              f"available: {', '.join(RENDERERS)}", file=sys.stderr)
        return 2

    try:
        stats = Client(token).stats(args.user, set(excluded))
    except GitHubError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in wanted:
        if name == "languages":
            svg = RENDERERS[name](stats, theme, args.language_limit, excluded)
        else:
            svg = RENDERERS[name](stats, theme)
        (out / f"{name}.svg").write_text(svg)
        print(f"wrote {out / f'{name}.svg'}")

    if args.badge:
        badge = {
            "schemaVersion": 1,
            "label": "contributions (last year)",
            "message": f"{stats.total_contributions:,}",
            "color": theme.accent.lstrip("#"),
            "namedLogo": "github",
            "logoColor": "white",
        }
        (out / "contributions.json").write_text(json.dumps(badge, indent=2) + "\n")
        print(f"wrote {out / 'contributions.json'}")

    if stats.restricted:
        print(f"\nnote: {stats.restricted:,} contributions are hidden because "
              f"'Include private contributions on my profile' is off.\n"
              f"      Settings -> Public profile -> Contributions & activity.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
