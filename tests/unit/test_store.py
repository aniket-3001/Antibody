import pytest

from api.memory import store


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path):
    store.init_db(tmp_path)
    yield


def test_ensure_reporter_creates_with_default_trust():
    trust = store.ensure_reporter("r_abc")
    assert trust == 0.3
    assert store.ensure_reporter("r_abc") == 0.3


def test_bump_trust_clamped_0_to_1():
    store.ensure_reporter("r_x")
    store.bump_trust("r_x", 10.0)
    assert store.ensure_reporter("r_x") == 1.0
    store.bump_trust("r_x", -10.0)
    assert store.ensure_reporter("r_x") == 0.0


def test_upsert_family_merges_tactics_and_lures():
    store.upsert_family("toll_scam", summary="first", tactics=["urgency_pressure"], lures=["toll_road"])
    store.upsert_family("toll_scam", summary="", tactics=["payment_demand"], lures=["toll_road"])
    fam = store.get_family("toll_scam")
    assert fam["summary"] == "first"
    assert set(fam["tactics"]) == {"urgency_pressure", "payment_demand"}
    assert fam["lures"] == ["toll_road"]


def test_get_family_missing_returns_none():
    assert store.get_family("nope") is None


def test_add_report_and_get_report_roundtrip():
    store.add_report(
        "rep_1", "some scam text", "sms", "toll_scam", "r_1",
        indicators=[{"kind": "url_domain", "value": "bad.biz"}],
        tactics=["urgency_pressure"], lures=["toll_road"],
    )
    rep = store.get_report("rep_1")
    assert rep["normalized_text"] == "some scam text"
    assert rep["family_name"] == "toll_scam"
    assert rep["indicators"][0]["value"] == "bad.biz"
    assert rep["is_control"] is False


def test_prune_report_excludes_from_active_reports():
    store.add_report("rep_1", "text", "sms", None, "r_1")
    store.add_report("rep_2", "text2", "sms", None, "r_1")
    store.prune_report("rep_1")
    active_ids = {r["id"] for r in store.active_reports()}
    assert active_ids == {"rep_2"}


def test_set_outcome_found_vs_missing():
    store.add_report("rep_1", "text", "sms", "fam_a", "r_1")
    found, family = store.set_outcome("rep_1", "confirmed_scam")
    assert found is True
    assert family == "fam_a"

    found2, family2 = store.set_outcome("does_not_exist", "confirmed_scam")
    assert found2 is False
    assert family2 is None


def test_lookup_indicator_case_and_whitespace_insensitive():
    store.upsert_indicator("Bad-Site.biz ", "url_domain", "toll_scam")
    hit = store.lookup_indicator("  bad-site.biz")
    assert hit["family_name"] == "toll_scam"


def test_lookup_indicator_missing_returns_none():
    assert store.lookup_indicator("unknown.biz") is None


def test_trust_weighted_reporters_sums_distinct_trusted_reporters():
    store.ensure_reporter("r_1")
    store.ensure_reporter("r_2")
    store.bump_trust("r_1", 0.2)  # -> 0.5
    store.add_report("rep_1", "t1", "sms", "fam_a", "r_1")
    store.add_report("rep_2", "t2", "sms", "fam_a", "r_2")
    total = store.trust_weighted_reporters("fam_a")
    assert total == pytest.approx(0.5 + 0.3)


def test_trust_weighted_reporters_excludes_legit_outcome():
    store.ensure_reporter("r_1")
    store.add_report("rep_1", "t1", "sms", "fam_a", "r_1", outcome="actually_legit")
    assert store.trust_weighted_reporters("fam_a") == 0.0


def test_family_report_count_excludes_pruned_and_legit():
    store.add_report("rep_1", "t1", "sms", "fam_a", "r_1")
    store.add_report("rep_2", "t2", "sms", "fam_a", "r_1", outcome="actually_legit")
    store.add_report("rep_3", "t3", "sms", "fam_a", "r_1")
    store.prune_report("rep_3")
    assert store.family_report_count("fam_a") == 1


def test_shared_tactic_map_only_includes_tactics_used_by_2plus_families():
    store.upsert_family("fam_a", tactics=["urgency_pressure", "payment_demand"])
    store.upsert_family("fam_b", tactics=["urgency_pressure"])
    store.upsert_family("fam_c", tactics=["romance_grooming"])
    shared = store.shared_tactic_map()
    tactics = {s["tactic"] for s in shared}
    assert "urgency_pressure" in tactics
    assert "payment_demand" not in tactics
    assert "romance_grooming" not in tactics


def test_guidance_roundtrip():
    assert store.get_guidance("fam_a") is None
    store.set_guidance("fam_a", ["do this"], ["report here"], ["recover like this"])
    g = store.get_guidance("fam_a")
    assert g["do_now"] == ["do this"]
    assert g["report_to"] == ["report here"]
    assert g["recovery"] == ["recover like this"]
