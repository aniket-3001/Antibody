from api.memory.indicators import extract_indicators, tag_lures, tag_tactics


def test_extract_url_domain():
    out = extract_indicators("Reschedule your delivery at http://usps-redelivery-fee.com/pay")
    domains = [i["value"] for i in out if i["kind"] == "url_domain"]
    assert "usps-redelivery-fee.com" in domains


def test_safe_hosts_excluded():
    out = extract_indicators("Track your package at https://www.usps.com/track")
    assert all(i["value"] != "usps.com" for i in out)


def test_extract_email_sender():
    out = extract_indicators("Contact billing@totally-not-usps.co for help")
    senders = [i["value"] for i in out if i["kind"] == "sender"]
    assert "billing@totally-not-usps.co" in senders


def test_extract_phone_normalizes_to_e164_ish():
    out = extract_indicators("Call us now at (555) 123-4567 to confirm.")
    phones = [i["value"] for i in out if i["kind"] == "phone"]
    assert phones == ["+15551234567"]


def test_extract_btc_wallet():
    out = extract_indicators("Send payment to bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq now.")
    wallets = [i["value"] for i in out if i["kind"] == "crypto_wallet"]
    assert wallets


def test_extract_eth_wallet():
    out = extract_indicators("Send to 0x32Be343B94f860124dC4fEe278FDCBD38C102D88 immediately.")
    wallets = [i["value"] for i in out if i["kind"] == "crypto_wallet"]
    assert wallets == ["0x32be343b94f860124dc4fee278fdcbd38c102d88"]


def test_extract_gift_card_ask():
    out = extract_indicators("Please pay with a Google Play gift card to clear this fee.")
    kinds = [i["kind"] for i in out]
    assert "gift_card_ask" in kinds


def test_extract_indicators_dedupes():
    out = extract_indicators("Visit http://scam-site.biz or http://scam-site.biz again.")
    domains = [i["value"] for i in out if i["kind"] == "url_domain"]
    assert domains == ["scam-site.biz"]


def test_extract_indicators_no_false_positives_on_legit_text():
    out = extract_indicators("Your dentist appointment is tomorrow at 10:00 AM. Reply C to confirm.")
    assert out == []


def test_tag_tactics_urgency_and_credential_harvest():
    tactics = tag_tactics("URGENT: verify your account immediately or it will be suspended.")
    assert "urgency_pressure" in tactics
    assert "credential_harvest" in tactics


def test_tag_lures_package_delivery():
    lures = tag_lures("Your USPS package delivery could not be completed, small fee required.")
    assert "package_delivery" in lures


def test_tag_tactics_empty_for_neutral_text():
    assert tag_tactics("See you at lunch tomorrow.") == []
