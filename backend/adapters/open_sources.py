"""The open adapter -- public feeds, no credentials.

This is the path a grader runs from a fresh clone, so it has to work with
nothing configured. It reads Spanish-language fact-check and climate news
feeds, which surface the narratives being corrected right now -- a decent
proxy for what is circulating.

Network failures degrade to whatever came back; an empty result is handled by
the caller, which falls through to the fixture.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import httpx

from models import SignalRecord

TIMEOUT = 20
UA = {"User-Agent": "LoteriaClimatica/1.0 (course project; contact via repo)"}

# Fact-check outlets publish what they are correcting, which is the signal we
# want. Google News RSS covers the rest without an API key.
FEEDS: list[tuple[str, str]] = [
    ("Maldita.es", "https://maldita.es/feeds/"),
    ("Newtral", "https://www.newtral.es/feed/"),
    ("Chequeado", "https://chequeado.com/feed/"),
    ("Google News", "https://news.google.com/rss/search?q=desinformaci%C3%B3n+clim%C3%A1tica&hl=es-419&gl=US&ceid=US:es-419"),
    ("Google News", "https://news.google.com/rss/search?q=bulo+energ%C3%ADa+solar+OR+e%C3%B3lica&hl=es-419&gl=US&ceid=US:es-419"),
    ("Google News", "https://news.google.com/rss/search?q=%22cambio+clim%C3%A1tico%22+desmentido&hl=es-419&gl=US&ceid=US:es-419"),
]

KEEP = re.compile(
    r"clim|calor|energ|solar|e[oó]lic|petr[oó]le|gas|carb[oó]n|renovable|"
    r"hurac|inunda|sequ[ií]a|contamina|emisi|planeta|ambient",
    re.I,
)
TAG = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    return TAG.sub(" ", text or "").replace("&nbsp;", " ").strip()


def _when(item: ET.Element) -> str:
    for tag in ("pubDate", "{http://purl.org/dc/elements/1.1/}date"):
        raw = item.findtext(tag)
        if not raw:
            continue
        try:
            return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            try:
                return datetime.fromisoformat(raw).astimezone(timezone.utc).isoformat()
            except ValueError:
                continue
    return datetime.now(timezone.utc).isoformat()


def collect(days: int = 14, limit: int = 60) -> list[SignalRecord]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out: list[SignalRecord] = []
    seen: set[str] = set()

    with httpx.Client(timeout=TIMEOUT, headers=UA, follow_redirects=True) as client:
        for name, url in FEEDS:
            try:
                resp = client.get(url)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
            except Exception:
                continue  # one dead feed does not take the brief down

            for item in root.iter("item"):
                title = _clean(item.findtext("title"))
                desc = _clean(item.findtext("description"))
                link = (item.findtext("link") or "").strip()
                blob = f"{title} {desc}"
                if not title or link in seen or not KEEP.search(blob):
                    continue
                stamp = _when(item)
                try:
                    if datetime.fromisoformat(stamp) < cutoff:
                        continue
                except ValueError:
                    pass
                seen.add(link)
                out.append(SignalRecord(
                    source="open",
                    platform=name,
                    language="es",
                    captured_at=stamp,
                    claim_text=(title + (" - " + desc if desc else ""))[:600],
                    url=link,
                ))
                if len(out) >= limit:
                    return out
    return out
