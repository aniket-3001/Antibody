"""Verdict engine (M3) — orchestrates the three-signal match → fusion → band →
cited explanation → guidance. Pure-ish glue over the memory layer.

Signal sourcing (spec §5):
  ① indicator  — exact known-bad IOC lookup in the ops store   (deterministic)
  ② semantic   — nearest prior report by meaning                (local index / Cognee)
  ③ structural — fraction of the family's signature tactics/lures matched
Plus corroboration (trust-weighted distinct reporters) and the family prior.

The cited human-readable EXPLANATION comes from Cognee GRAPH_COMPLETION when an
LLM key is present; otherwise a graph-grounded template keeps the demo alive.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from api.config import settings
from api.memory import indicators as ind
from api.memory import store
from api.memory.confidence import (
    Signals,
    corroboration_strength,
    decide,
    family_prior,
)
from api.memory.memory_service import MemoryUnavailable, memory_service
from api.memory.semantic import semantic_index

log = logging.getLogger("antibody.verdict")

BAND_LABEL = {
    "confirmed": "Confirmed scam",
    "likely": "Likely scam",
    "suspicious": "Suspicious",
    "unrecognized": "Not recognized",
}
BAND_EMOJI = {"confirmed": "🔴", "likely": "🟠", "suspicious": "🟡", "unrecognized": "🟢"}


def _days_since(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
    except ValueError:
        return None


def _structural_strength(family: str | None, tactics: list[str], lures: list[str]) -> float:
    if not family:
        return 0.0
    fam = store.get_family(family)
    if not fam:
        return 0.0
    sig = set(fam.get("tactics") or []) | set(fam.get("lures") or [])
    if not sig:
        return 0.0
    got = (set(tactics) | set(lures)) & sig
    return len(got) / len(sig)


async def _cognee_explanation(text: str, family: str | None) -> dict:
    """Cited, human-readable 'what this is + the tell' from the graph."""
    q = (
        f"A user forwarded this suspicious message: \"{text[:600]}\". "
        "Which known scam family does it match? Explain in 2-3 sentences what it "
        "is and the clearest tell that gives it away, citing prior reports."
    )
    try:
        res = await memory_service.search(q, "GRAPH_COMPLETION", top_k=8)
        if res.get("available") and res.get("answer", "").strip():
            return {"text": res["answer"].strip(), "citations": res.get("citations", []),
                    "source": "cognee_graph"}
    except MemoryUnavailable:
        pass
    except Exception:
        log.exception("cognee explanation failed")
    return {"text": "", "citations": [], "source": "fallback"}


def _template_explanation(family: str | None, reasons: list[str]) -> str:
    if family:
        fam = store.get_family(family)
        summary = (fam or {}).get("summary") or ""
        base = f"This matches the {family.replace('_', ' ')} pattern. {summary}".strip()
    else:
        base = "This doesn't match any known scam family in our memory yet."
    if reasons:
        base += " We flagged it because it " + "; ".join(reasons) + "."
    return base


async def assess(
    normalized_text: str,
    channel: str | None = None,
    reporter_id: str | None = None,
    provided_indicators: list[dict] | None = None,
) -> dict:
    text = normalized_text.strip()

    # --- extract ---
    indicators = provided_indicators or ind.extract_indicators(text)
    tactics = ind.tag_tactics(text)
    lures = ind.tag_lures(text)

    # --- ① indicator signal (deterministic exact lookup) ---
    s_ind = 0.0
    ind_family = None
    ind_reason = ""
    for i in indicators:
        hit = store.lookup_indicator(i["value"])
        if hit:
            s_ind = 0.98
            ind_family = hit["family_name"]
            ind_reason = f"matches a known-bad {hit['kind'].replace('_', ' ')}: {hit['value']}"
            break

    # --- ② semantic signal ---
    sem = semantic_index.best_family(text)
    s_sem = sem["strength"]
    # Only treat semantic as a family match when it clears the rescale floor
    # (strength > 0). looks_legit means the message resembles a legit control —
    # the asymmetric gate: recognize it as legit, never accuse.
    sem_family = sem["family"] if (s_sem > 0 and not sem.get("looks_legit")) else None

    # candidate family: indicator wins, else semantic
    family = ind_family or sem_family

    # --- ③ structural signal ---
    s_struct = _structural_strength(family, tactics, lures)

    # A family (and thus its corroboration/prior) may only be inherited when
    # THIS report has a real primary signal tying it to that family. Otherwise
    # corroboration/family prior alone could manufacture a false positive.
    primary_match = (s_ind >= 0.9) or (s_sem > 0) or (s_struct >= 0.4)
    if family and not primary_match:
        family = None
        s_struct = 0.0

    # --- corroboration + family prior ---
    trust_weight = store.trust_weighted_reporters(family) if family else 0.0
    s_corr = corroboration_strength(trust_weight)
    report_count = store.family_report_count(family) if family else 0
    fam_row = store.get_family(family) if family else None
    s_fam = family_prior(report_count, _days_since((fam_row or {}).get("last_seen")))

    sig = Signals(
        indicator=s_ind, semantic=s_sem, structural=s_struct,
        corroboration=s_corr, family=s_fam,
        detail={
            "indicator_reason": ind_reason,
            "semantic_reason": (
                f"reads almost identically to prior reports (similarity {sem['cosine']:.0%})"
                if s_sem > 0 else ""
            ),
            "structural_reason": (
                f"uses {int(round(s_struct * 100))}% of this family's signature tactics"
                if s_struct > 0 else ""
            ),
            "corroboration_reason": (
                f"independently reported {report_count}× by the community"
                if report_count else ""
            ),
            "reporter_weight": trust_weight,
        },
    )

    verdict = decide(
        sig,
        confirmed_th=settings.band_confirmed,
        likely_th=settings.band_likely,
        suspicious_th=settings.band_suspicious,
    )

    # --- explanation (Cognee first, template fallback) ---
    explanation = {"text": "", "citations": [], "source": "fallback"}
    if verdict.band != "unrecognized" and family:
        explanation = await _cognee_explanation(text, family)
    if not explanation["text"]:
        explanation = {
            "text": _template_explanation(family, verdict.reasons),
            "citations": [],
            "source": "fallback",
        }

    # --- guidance ---
    guidance = store.get_guidance(family) if family else None
    if not guidance:
        guidance = _generic_guidance()

    # --- shared-tactic graph beat (spec §16 beat 3) ---
    shared = []
    if family:
        fam_tactics = set((fam_row or {}).get("tactics") or [])
        for entry in store.shared_tactic_map():
            if entry["tactic"] in fam_tactics and family in entry["families"]:
                others = [f for f in entry["families"] if f != family]
                if others:
                    shared.append({"tactic": entry["tactic"], "also_used_by": others})

    return {
        "band": verdict.band,
        "band_label": BAND_LABEL[verdict.band],
        "band_emoji": BAND_EMOJI[verdict.band],
        "confidence": verdict.confidence,
        "family": family,
        "family_display": family.replace("_", " ").title() if family else None,
        "report_count": report_count,
        "first_seen": store.family_first_seen(family) if family else None,
        "reasons": verdict.reasons,
        "signals": {
            "indicator": round(sig.indicator, 3),
            "semantic": round(sig.semantic, 3),
            "structural": round(sig.structural, 3),
            "corroboration": round(sig.corroboration, 3),
            "family": round(sig.family, 3),
        },
        "indicators": indicators,
        "tactics": tactics,
        "lures": lures,
        "highlights": ind.find_highlight_spans(text, tactics=tactics, lures=lures),
        "explanation": explanation["text"],
        "explanation_source": explanation["source"],
        "citations": explanation["citations"],
        "guidance": guidance,
        "shared_tactics": shared,
    }


def _generic_guidance() -> dict:
    return {
        "do_now": [
            "Don't click any links or call any numbers in the message.",
            "Don't share codes, passwords, or payment details.",
            "If it claims to be a company you use, contact them via their official app or website.",
        ],
        "report_to": [
            "US: forward texts to 7726 (SPAM); report at reportfraud.ftc.gov",
            "UK: forward texts to 7726; report at actionfraud.police.uk",
        ],
        "recovery": [
            "If you already paid or shared details, contact your bank immediately.",
            "Change any password you entered and enable two-factor authentication.",
        ],
    }
