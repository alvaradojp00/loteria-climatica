"""The mailing list.

Storing people's contact details is a different kind of commitment from the
rest of this project, so the rules are in the code rather than in a policy
page nobody reads:

  * Consent is required and recorded, with the timestamp and the wording they
    actually agreed to.
  * Every row carries an unsubscribe token from the moment it is created.
  * Unsubscribing is a real delete, not a flag.
  * Nothing is shared with anyone. There is one export, it is behind the admin
    password, and it is for the person who runs this list.
"""

from __future__ import annotations

import csv
import io
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config import DATA

DB = DATA / "subscribers.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    zip TEXT,
    phone TEXT,
    lang TEXT,
    sms_consent INTEGER DEFAULT 0,
    consent_text TEXT NOT NULL,
    consent_at TEXT NOT NULL,
    source TEXT,
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS subs_email ON subscribers(email);
"""

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


@contextmanager
def conn():
    DATA.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        c.executescript(SCHEMA)
        yield c
        c.commit()
    finally:
        c.close()


def subscribe(name: str, email: str, zip_code: str = "", phone: str = "",
              lang: str = "es", sms_consent: bool = False,
              consent_text: str = "", source: str = "web") -> dict:
    email = email.strip().lower()
    if not EMAIL.match(email):
        raise ValueError("that email address does not look right")
    if not name.strip():
        raise ValueError("a name is required")
    if not consent_text.strip():
        raise ValueError("consent wording must be recorded")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    token = secrets.token_urlsafe(24)
    with conn() as c:
        existing = c.execute("SELECT token FROM subscribers WHERE email=?",
                             (email,)).fetchone()
        if existing:
            # re-subscribing refreshes the details rather than duplicating
            c.execute(
                "UPDATE subscribers SET name=?, zip=?, phone=?, lang=?, "
                "sms_consent=?, consent_text=?, consent_at=? WHERE email=?",
                (name.strip(), zip_code.strip(), phone.strip(), lang,
                 int(sms_consent), consent_text, now, email),
            )
            return {"status": "updated", "token": existing["token"]}
        c.execute(
            "INSERT INTO subscribers (name, email, zip, phone, lang, sms_consent,"
            " consent_text, consent_at, source, token, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (name.strip(), email, zip_code.strip(), phone.strip(), lang,
             int(sms_consent), consent_text, now, source, token, now),
        )
    return {"status": "subscribed", "token": token}


def unsubscribe(token: str) -> bool:
    with conn() as c:
        cur = c.execute("DELETE FROM subscribers WHERE token=?", (token,))
        return cur.rowcount > 0


def count() -> dict:
    with conn() as c:
        total = c.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
        sms = c.execute("SELECT COUNT(*) FROM subscribers WHERE sms_consent=1").fetchone()[0]
        es = c.execute("SELECT COUNT(*) FROM subscribers WHERE lang='es'").fetchone()[0]
        recent = c.execute(
            "SELECT COUNT(*) FROM subscribers WHERE created_at >= datetime('now','-7 days')"
        ).fetchone()[0]
    return {"total": total, "sms_consented": sms, "spanish": es, "last_7_days": recent}


def rows() -> list[dict]:
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM subscribers ORDER BY created_at DESC").fetchall()]


def to_csv() -> str:
    data = rows()
    buf = io.StringIO()
    cols = ["name", "email", "zip", "phone", "lang", "sms_consent",
            "consent_text", "consent_at", "source", "created_at"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in data:
        w.writerow(r)
    return buf.getvalue()


def audience(channel: str = "email", lang: str | None = None) -> list[dict]:
    """Who may actually be contacted on a given channel.

    SMS is a separate consent from email, and this is the only place that
    decides who is in a send. A blast cannot reach somebody who did not opt
    in to that channel because the list it is handed excludes them.
    """
    out = []
    for r in rows():
        if lang and r["lang"] != lang:
            continue
        if channel == "sms":
            if not r["sms_consent"] or not r["phone"]:
                continue
        out.append({"name": r["name"], "email": r["email"],
                    "phone": r["phone"], "lang": r["lang"]})
    return out
