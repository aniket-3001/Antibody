"""Deterministic IOC extraction — signal ① of the three-signal match (spec §5).

Hard indicators (URL domain, phone, crypto wallet, sender, gift-card ask) are
the cheapest and strongest single signal: an exact match against a known-bad
Indicator is near-certainty and is what gates the CONFIRMED band (spec §7).

Also here: a lightweight keyword tagger for tactics/lures. When an LLM key is
present, Cognee's cognify() extracts these richly; when it is not, this fallback
keeps the STRUCTURAL signal (③) alive so the demo never goes dark.
"""
from __future__ import annotations

import re

# --- URL / domain ---
_URL_RE = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?:/[^\s]*)?", re.I)
# Common legitimate hosts we should never treat as a scam indicator
_SAFE_HOSTS = {
    "usps.com", "ups.com", "fedex.com", "dhl.com", "irs.gov", "gov.uk",
    "paypal.com", "amazon.com", "apple.com", "microsoft.com", "google.com",
    "chase.com", "bankofamerica.com", "wellsfargo.com", "hsbc.com",
}

_PHONE_RE = re.compile(r"(?<!\w)(\+?\d[\d\s().-]{7,}\d)(?!\w)")
_EMAIL_RE = re.compile(r"\b[a-z0-9._%+-]+@([a-z0-9.-]+\.[a-z]{2,})\b", re.I)
# BTC / ETH-ish wallet shapes
_BTC_RE = re.compile(r"\b(bc1[a-z0-9]{20,}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")
_ETH_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")

_GIFT_CARD_RE = re.compile(
    r"\b(gift\s?card|google\s?play|steam\s?card|itunes|apple\s?card|amazon\s?card)\b", re.I
)


def _norm_phone(raw: str) -> str:
    digits = re.sub(r"[^\d+]", "", raw)
    if not digits.startswith("+"):
        if len(digits) == 10:  # assume US
            digits = "+1" + digits
        elif len(digits) == 11 and digits.startswith("1"):
            digits = "+" + digits
        else:
            digits = "+" + digits
    return digits


def extract_indicators(text: str) -> list[dict]:
    """Return normalized indicator dicts: {kind, value}."""
    out: list[dict] = []
    seen: set[tuple] = set()

    def push(kind: str, value: str) -> None:
        key = (kind, value)
        if value and key not in seen:
            seen.add(key)
            out.append({"kind": kind, "value": value})

    for m in _URL_RE.finditer(text):
        host = m.group(1).lower().strip(".")
        # strip leading www.
        host = re.sub(r"^www\.", "", host)
        if host and host not in _SAFE_HOSTS and "." in host:
            push("url_domain", host)

    for m in _EMAIL_RE.finditer(text):
        domain = m.group(1).lower()
        if domain not in _SAFE_HOSTS:
            push("sender", m.group(0).lower())

    for m in _PHONE_RE.finditer(text):
        push("phone", _norm_phone(m.group(1)))

    for m in _BTC_RE.finditer(text):
        push("crypto_wallet", m.group(1))
    for m in _ETH_RE.finditer(text):
        push("crypto_wallet", m.group(0).lower())

    if _GIFT_CARD_RE.search(text):
        push("gift_card_ask", "gift_card")

    return out


# --- Keyword tactic/lure tagger (LLM-free structural fallback) ---

_TACTIC_KEYWORDS: dict[str, list[str]] = {
    "fake_delivery_fee": ["redelivery", "delivery fee", "reschedule delivery", "small fee",
                          "customs fee", "shipping fee", "unpaid toll", "toll fee"],
    "urgency_pressure": ["urgent", "immediately", "within 24", "act now", "final notice",
                         "suspended", "will be closed", "last warning", "expires today"],
    "spoofed_sender": ["on behalf of", "official", "do not reply", "verified sender"],
    "credential_harvest": ["verify your account", "confirm your identity", "log in to",
                           "update your details", "enter your password", "one-time code",
                           "otp", "verification code", "2fa"],
    "payment_demand": ["pay", "$", "£", "€", "wire", "bank transfer", "payment required"],
    "gift_card_payment": ["gift card", "google play", "steam card", "itunes", "apple card"],
    "callback_number": ["call us", "call this number", "callback", "call immediately",
                        "contact support at", "call our"],
    "impersonation": ["this is your bank", "from the irs", "hmrc", "social security",
                      "amazon security", "microsoft support", "we detected"],
    "refund_bait": ["you are eligible", "refund", "you have won", "claim your", "rebate"],
    "romance_grooming": ["my dear", "trust me", "invest together", "our future", "lonely"],
}

_LURE_KEYWORDS: dict[str, list[str]] = {
    "package_delivery": ["package", "parcel", "delivery", "shipment", "usps", "ups", "fedex", "dhl"],
    "tax_refund": ["tax", "irs", "hmrc", "refund", "rebate"],
    "bank_security": ["bank", "account", "card", "fraud alert", "unauthorized"],
    "tech_support": ["virus", "computer", "microsoft", "apple support", "subscription",
                     "renewal", "geek squad", "norton", "mcafee"],
    "toll_road": ["toll", "e-zpass", "ez pass", "highway"],
    "crypto_investment": ["crypto", "bitcoin", "investment", "trading", "returns", "wallet"],
    "romance": ["love", "relationship", "lonely", "met you", "dear"],
    "prize_lottery": ["won", "prize", "lottery", "winner", "reward"],
    "job_offer": ["job", "work from home", "hiring", "position", "salary"],
}


def _match_keywords(text: str, table: dict[str, list[str]]) -> list[str]:
    low = text.lower()
    hits = []
    for label, kws in table.items():
        if any(kw in low for kw in kws):
            hits.append(label)
    return hits


def tag_tactics(text: str) -> list[str]:
    return _match_keywords(text, _TACTIC_KEYWORDS)


def tag_lures(text: str) -> list[str]:
    return _match_keywords(text, _LURE_KEYWORDS)


# --- Highlight spans (UI-only: where each already-tagged signal sits in the text) ---

_INDICATOR_LABEL = {
    "url_domain": "link", "sender": "sender", "phone": "phone",
    "crypto_wallet": "crypto wallet", "gift_card_ask": "gift card",
}


def find_highlight_spans(text: str, tactics: list[str] | None = None,
                          lures: list[str] | None = None) -> list[dict]:
    """Character spans for indicators/tactics/lures so the UI can underline the
    exact words that drove the verdict, instead of just listing them separately.

    Re-locates the same matches extract_indicators()/tag_tactics()/tag_lures()
    already found (rather than re-deciding what counts) so highlights never
    drift from the actual verdict reasons."""
    spans: list[dict] = []

    for m in _URL_RE.finditer(text):
        host = re.sub(r"^www\.", "", m.group(1).lower().strip("."))
        if host and host not in _SAFE_HOSTS and "." in host:
            spans.append({"start": m.start(), "end": m.end(), "kind": "indicator",
                          "label": _INDICATOR_LABEL["url_domain"]})

    for m in _EMAIL_RE.finditer(text):
        if m.group(1).lower() not in _SAFE_HOSTS:
            spans.append({"start": m.start(), "end": m.end(), "kind": "indicator",
                          "label": _INDICATOR_LABEL["sender"]})

    for m in _PHONE_RE.finditer(text):
        spans.append({"start": m.start(), "end": m.end(), "kind": "indicator",
                      "label": _INDICATOR_LABEL["phone"]})

    for m in _BTC_RE.finditer(text):
        spans.append({"start": m.start(), "end": m.end(), "kind": "indicator",
                      "label": _INDICATOR_LABEL["crypto_wallet"]})
    for m in _ETH_RE.finditer(text):
        spans.append({"start": m.start(), "end": m.end(), "kind": "indicator",
                      "label": _INDICATOR_LABEL["crypto_wallet"]})

    gift = _GIFT_CARD_RE.search(text)
    if gift:
        spans.append({"start": gift.start(), "end": gift.end(), "kind": "indicator",
                      "label": _INDICATOR_LABEL["gift_card_ask"]})

    low = text.lower()
    for label in tactics or []:
        for kw in _TACTIC_KEYWORDS.get(label, []):
            idx = low.find(kw)
            if idx != -1:
                spans.append({"start": idx, "end": idx + len(kw), "kind": "tactic", "label": label})
                break
    for label in lures or []:
        for kw in _LURE_KEYWORDS.get(label, []):
            idx = low.find(kw)
            if idx != -1:
                spans.append({"start": idx, "end": idx + len(kw), "kind": "lure", "label": label})
                break

    spans.sort(key=lambda s: s["start"])
    return spans
