from .activity import render as activity
from .languages import render as languages
from .stats import render as stats

RENDERERS = {"stats": stats, "languages": languages, "activity": activity}
__all__ = ["stats", "languages", "activity", "RENDERERS"]
