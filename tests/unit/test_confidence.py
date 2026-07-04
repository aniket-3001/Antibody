from api.memory.confidence import (
    Signals,
    corroboration_strength,
    decide,
    family_prior,
    fuse,
)


def test_corroboration_strength_grows_with_reporters_but_bounded():
    low = corroboration_strength(0.0)
    mid = corroboration_strength(3.0)
    high = corroboration_strength(50.0)
    assert low == 0.0
    assert low < mid < high
    assert high < 1.0


def test_family_prior_increases_with_report_count():
    assert family_prior(0, None) < family_prior(10, None)


def test_family_prior_decays_with_staleness():
    fresh = family_prior(10, days_since_last=1)
    stale = family_prior(10, days_since_last=180)
    assert stale < fresh


def test_fuse_one_strong_signal_dominates():
    sig = Signals(indicator=1.0)
    assert fuse(sig) >= 0.9


def test_fuse_no_signals_is_zero():
    assert fuse(Signals()) == 0.0


def test_decide_known_bad_indicator_with_corroboration_is_confirmed():
    sig = Signals(
        indicator=1.0,
        structural=0.8,
        corroboration=corroboration_strength(5.0),
        detail={"reporter_weight": 5.0},
    )
    v = decide(sig)
    assert v.band == "confirmed"


def test_decide_semantic_only_never_reaches_confirmed():
    """The single most important safety property: a legit message that merely
    *resembles* a scam family by meaning alone must never be hard-accused."""
    sig = Signals(semantic=1.0, family=1.0, corroboration=corroboration_strength(50.0),
                  detail={"reporter_weight": 50.0})
    v = decide(sig)
    assert v.band != "confirmed"


def test_decide_confirmed_requires_corroboration_floor_without_indicator():
    """Structural-only (no known-bad indicator) with too few corroborating
    reporters must not reach confirmed, even if fused confidence is high."""
    sig = Signals(
        structural=1.0, semantic=1.0, family=1.0,
        corroboration=corroboration_strength(1.0),
        detail={"reporter_weight": 1.0},
    )
    v = decide(sig)
    assert v.band != "confirmed"


def test_decide_no_signals_is_unrecognized():
    v = decide(Signals())
    assert v.band == "unrecognized"


def test_decide_weak_signal_is_suspicious_not_likely():
    v = decide(Signals(semantic=0.5))
    assert v.band in ("suspicious", "unrecognized")
    assert v.band != "confirmed"
