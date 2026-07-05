"""Antibody's Cognee ontology — the ScamOntology graph_model for cognify().

Lifted from meetgraph's ontology.py pattern (lazy build, DataPoint subclasses,
typed fields become edges, metadata index_fields control embedding). The one
design decision that earns the "Best Use of Cognee" score (spec §4):

    Tactic and Lure are SHARED nodes across families.

Same label string → same node across every report and family that uses it. That
is what turns a flat pile of reports into a graph you can *traverse* — "this new
campaign uses the same fake-fee tactic as the tech-support scam" is a fact a
vector store alone cannot represent. Do NOT duplicate Tactic/Lure per report.

Built lazily so `api` imports cleanly before cognee finishes loading.
"""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def build_graph_model():
    """Return the root DataPoint model for cognify(graph_model=...)."""

    from cognee.low_level import DataPoint

    class Tactic(DataPoint):
        """A reusable manipulation technique. SHARED across families."""

        label: str  # "fake_delivery_fee", "urgency_pressure", "spoofed_sender", ...
        category: str | None = None  # social_engineering | payment | impersonation
        metadata: dict = {"index_fields": ["label"]}

    class Lure(DataPoint):
        """The hook / pretext the scam hides behind. SHARED across families."""

        label: str  # "package_delivery", "tax_refund", "bank_security", ...
        metadata: dict = {"index_fields": ["label"]}

    class Channel(DataPoint):
        label: str  # sms | email | voice_call | whatsapp
        metadata: dict = {"index_fields": ["label"]}

    class Indicator(DataPoint):
        """A hard IOC — the deterministic fast-path match key."""

        kind: str  # url_domain | phone | sender | crypto_wallet | gift_card_ask
        value: str  # normalized (lowercased domain, E.164 phone, ...)
        metadata: dict = {"index_fields": ["value"]}

    class ScamFamily(DataPoint):
        """The cluster a report belongs to — 'USPS redelivery-fee scam'."""

        name: str
        summary: str
        first_seen: str | None = None
        last_seen: str | None = None
        tactics: list[Tactic] = []
        lures: list[Lure] = []
        metadata: dict = {"index_fields": ["name", "summary"]}

    class ScamReport(DataPoint):
        """One submission — the atom that accumulates. Root of the graph_model."""

        normalized_text: str
        channel: Channel | None = None
        family: ScamFamily | None = None
        tactics: list[Tactic] = []
        lures: list[Lure] = []
        indicators: list[Indicator] = []
        reported_at: str | None = None
        outcome: str | None = None  # confirmed_scam | i_got_scammed | actually_legit
        metadata: dict = {"index_fields": ["normalized_text"]}

    return ScamReport
