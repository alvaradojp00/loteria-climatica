"""Ingest adapters for El Boletin.

One record shape, three sources. The app uses the richest adapter whose
credentials are present and says on the page which one it used, so the brief
works from a fresh clone with no keys at all.

    fixture  -- committed sample, always available, no network
    open     -- public feeds and fact-check outlets, no credentials
    junkipedia -- the real monitoring platform, needs an entitled API key
"""

from __future__ import annotations

import os

from models import SignalRecord


def available() -> list[str]:
    names = ["fixture", "open"]
    if os.getenv("JUNKIPEDIA_API_KEY"):
        names.append("junkipedia")
    return names


def best() -> str:
    """Richest adapter that can actually run right now."""
    from adapters import junkipedia

    if os.getenv("JUNKIPEDIA_API_KEY") and junkipedia.entitled():
        return "junkipedia"
    return "open"


def collect(adapter: str, days: int = 14, limit: int = 60) -> list[SignalRecord]:
    from adapters import fixture, junkipedia, open_sources

    if adapter == "fixture":
        return fixture.collect(days, limit)
    if adapter == "junkipedia":
        return junkipedia.collect(days, limit)
    return open_sources.collect(days, limit)
