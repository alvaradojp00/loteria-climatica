"""Sending adapters — built, documented, dormant.

Same shape as the Junkipedia adapter: the integration exists and reports its
own status honestly, but it is switched off until credentials arrive. Until
then the workflow is manual — export the audience as CSV from El Taller and
send from whatever tool you already have.

That is a deliberate stopping point rather than an unfinished one. Sending to
a list carries obligations the rest of this project does not (deliverability,
unsubscribe handling, 10DLC registration for SMS), and wiring a provider in
before those are in place would make the feature look ready when it is not.

To switch a channel on later, set its keys in `.env` and nothing else changes:
the audience builder already decides who may be contacted, and it excludes
anyone who did not consent to that channel.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Channel:
    key: str
    label: str
    env: list[str]
    provider_hint: str
    blockers: list[str]

    @property
    def configured(self) -> bool:
        return all(os.getenv(v) for v in self.env)

    def status(self) -> dict:
        missing = [v for v in self.env if not os.getenv(v)]
        return {
            "channel": self.key,
            "label": self.label,
            "configured": self.configured,
            "missing_env": missing,
            "provider_hint": self.provider_hint,
            "blockers": self.blockers,
            "note": ("Connected." if self.configured else
                     "Not connected. Export the audience as CSV from El Taller "
                     "and send it from your own tool."),
        }


EMAIL = Channel(
    key="email",
    label="Email",
    env=["EMAIL_API_KEY", "EMAIL_FROM"],
    provider_hint="Resend, Mailgun, SendGrid or Buttondown",
    blockers=[
        "A domain you control, with SPF and DKIM records so mail is not filtered.",
        "A visible unsubscribe link in every send — the token already exists on every row.",
        "A physical mailing address in the footer (CAN-SPAM).",
    ],
)

SMS = Channel(
    key="sms",
    label="SMS",
    env=["SMS_ACCOUNT_SID", "SMS_AUTH_TOKEN", "SMS_FROM"],
    provider_hint="Twilio",
    blockers=[
        "A number, and A2P 10DLC brand and campaign registration with the carriers.",
        "Carriers review the opt-in flow, so the consent wording has to be shown to them.",
        "'Reply STOP to unsubscribe' in every message, honoured automatically.",
    ],
)

CHANNELS = {c.key: c for c in (EMAIL, SMS)}


def status() -> dict:
    return {
        "any_configured": any(c.configured for c in CHANNELS.values()),
        "channels": [c.status() for c in CHANNELS.values()],
        "manual_workflow": (
            "Download the CSV for the channel you want, then send from your own "
            "tool. The CSV carries the consent wording and timestamp for every "
            "person, and only includes people who opted in to that channel."
        ),
    }


def send(channel: str, audience: list[dict], subject: str, body: str) -> dict:
    """Deliberately not implemented. Kept so the call site is obvious later."""
    ch = CHANNELS.get(channel)
    if ch is None:
        raise ValueError(f"unknown channel {channel!r}")
    if not ch.configured:
        raise RuntimeError(
            f"{ch.label} is not connected (missing "
            f"{', '.join(v for v in ch.env if not os.getenv(v))}). "
            f"Export the CSV from El Taller and send manually."
        )
    raise NotImplementedError(
        f"{ch.label} credentials are present, but the provider call is not "
        f"written yet. Add it here once {ch.provider_hint} is chosen."
    )
