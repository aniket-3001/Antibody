from api.memory.semantic import SemanticIndex, rescale


def test_rescale_boundaries():
    assert rescale(0.0) == 0.0
    assert rescale(0.35) == 0.0
    assert rescale(0.85) == 1.0
    assert rescale(0.95) == 1.0
    assert 0.0 < rescale(0.6) < 1.0


def test_best_family_matches_reworded_scam_variant():
    idx = SemanticIndex()
    idx.add("r1", "toll_unpaid_fee_scam",
            "Your toll payment is overdue, pay a small fee now to avoid penalties.",
            is_control=False)
    result = idx.best_family(
        "You have an unpaid toll fee, a small payment is required immediately to avoid extra charges."
    )
    assert result["family"] == "toll_unpaid_fee_scam"
    assert result["looks_legit"] is False


def test_best_family_recognizes_legit_control():
    idx = SemanticIndex()
    idx.add("r1", "bank_otp_theft_scam",
            "Your bank account is suspended, verify your identity now by sharing your OTP code.",
            is_control=False)
    idx.add("c1", None,
            "Chase: A deposit of $1,240.00 posted to your checking account. View details in the Chase app.",
            is_control=True)
    result = idx.best_family(
        "Chase: A deposit of $980.00 posted to your checking account. View details in the Chase app."
    )
    assert result["looks_legit"] is True
    assert result["family"] is None


def test_best_family_empty_index_returns_no_match():
    idx = SemanticIndex()
    result = idx.best_family("anything at all")
    assert result["family"] is None
    assert result["looks_legit"] is False


def test_best_returns_top_k_sorted_by_cosine():
    idx = SemanticIndex()
    idx.add("r1", "fam_a", "verify your account immediately or it will be suspended")
    idx.add("r2", "fam_b", "completely unrelated text about lunch plans")
    hits = idx.best("verify your account now or it will be suspended", top_k=2)
    assert hits[0]["report_id"] == "r1"
    assert hits[0]["cosine"] >= hits[1]["cosine"]
