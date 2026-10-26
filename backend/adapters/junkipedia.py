"""Junkipedia adapter -- built, tested against the API, dormant.

Junkipedia is a social-media monitoring platform run by the Algorithmic
Transparency Institute. Its API is documented at
https://docs.junkipedia.org/reference-material/api/ and authenticates with an
OAuth2 bearer token.

Status as of 2026-10-25: the key in `.env` authenticates correctly, but every
endpoint returns

    403 {"code": "forbidden", "detail": "You cannot access the API because your
         organization does not have this permission."}

A deliberately invalid key returns a *different* error ("the authentication
token you have supplied is invalid"), which is how we know the credential is
real and the block is an organisation-level entitlement rather than a bad key.
The entitlement has been requested.

Nothing depends on this. `adapters.best()` falls back to the open adapter, and
El Boletin runs without it.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from models import SignalRecord

BASE = "https://www.junkipedia.org/api/v1"
TIMEOUT = 45


def _get(path: str, params: dict | None = None) -> tuple[int, str]:
    key = os.getenv("JUNKIPEDIA_API_KEY", "")
    url = f"{BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {key}", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:  # network down, DNS, etc.
        return 0, f"{type(exc).__name__}: {exc}"


def entitled() -> bool:
    """True when the key exists and the organisation may actually use the API."""
    if not os.getenv("JUNKIPEDIA_API_KEY"):
        return False
    status, _ = _get("posts", {"per_page": 1})
    return status == 200


def status_note() -> str:
    """Human-readable line for the brief page, so the source is never implied."""
    if not os.getenv("JUNKIPEDIA_API_KEY"):
        return "Junkipedia: no key configured."
    status, body = _get("posts", {"per_page": 1})
    if status == 200:
        return "Junkipedia: connected."
    try:
        detail = json.loads(body)["errors"][0]["detail"]
    except Exception:
        detail = body[:120]
    return f"Junkipedia: unavailable ({status}) - {detail}"


def collect(days: int = 14, limit: int = 60) -> list[SignalRecord]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    status, body = _get("posts", {
        "per_page": min(limit, 100),
        "published_at_from": since,
        "language_code": "es",
        "search": "clima OR climatico OR energia OR solar OR calor",
    })
    if status != 200:
        return []

    out: list[SignalRecord] = []
    for row in json.loads(body).get("data", []):
        a = row.get("attributes", {}) or {}
        out.append(SignalRecord(
            source="junkipedia",
            platform=a.get("channel_type") or a.get("platform") or "",
            language=a.get("language_code") or "es",
            captured_at=a.get("published_at") or "",
            claim_text=(a.get("search_data_fields", {}) or {}).get("description")
                       or a.get("post_body") or "",
            url=a.get("post_url") or "",
            reach_estimate=a.get("engagement_count"),
        ))
    return [r for r in out if r.claim_text.strip()][:limit]
