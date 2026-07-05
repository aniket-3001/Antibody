import json
import uuid
from datetime import datetime, timezone, timedelta
import random
from pathlib import Path

from api.memory import store
from api.intake import ingest

def _fake_report_id():
    return "rep_" + uuid.uuid4().hex[:12]

def _hours_ago(hrs):
    return (datetime.now(timezone.utc) - timedelta(hours=hrs)).isoformat()

FAMILIES = [
    {
        "name": "usps_smishing",
        "summary": "Fake USPS package delivery failure SMS messages linking to credential harvesting sites.",
        "tactics": ["urgency", "authority_impersonation", "link_obfuscation"],
        "lures": ["failed_delivery", "missing_address"],
        "channels": ["sms"],
        "guidance": {
            "do_now": ["Do not click the link.", "Check tracking directly on usps.com if expecting a package."],
            "report_to": ["Forward text to 7726 (SPAM).", "Report to US Postal Inspection Service."],
            "recovery": ["If you provided card details, cancel the card immediately."]
        },
        "indicators": [
            {"value": "usps-delivery-status.com", "kind": "domain"},
            {"value": "usps-post-office.net", "kind": "domain"}
        ],
        "templates": [
            "USPS: Your package could not be delivered due to an incomplete address. Please update it here: https://usps-delivery-status.com/update",
            "U.S. Postal Service: Action required. We attempted delivery today but failed. Reschedule at https://usps-post-office.net",
        ]
    },
    {
        "name": "paypal_suspension",
        "summary": "Phishing emails/texts claiming the victim's PayPal account will be permanently suspended unless verified.",
        "tactics": ["urgency", "threat", "link_obfuscation", "brand_impersonation"],
        "lures": ["account_suspension", "unauthorized_login"],
        "channels": ["email", "sms"],
        "guidance": {
            "do_now": ["Log into PayPal directly using a browser, do not use the link in the message."],
            "report_to": ["Forward the email to spoof@paypal.com."],
            "recovery": ["Change PayPal password immediately.", "Enable 2FA on PayPal."]
        },
        "indicators": [
            {"value": "paypal-secure-verify.com", "kind": "domain"},
            {"value": "support@paypal-security-update.com", "kind": "email"}
        ],
        "templates": [
            "PayPal Alert: We detected an unusual login from an unrecognized device. Your account will be locked in 24 hours. Verify here: https://paypal-secure-verify.com",
            "Dear Customer, your PayPal account is restricted. Please confirm your identity to restore access.",
        ]
    },
    {
        "name": "irs_impersonation",
        "summary": "Threatening calls or messages from fake IRS agents demanding immediate payment for back taxes.",
        "tactics": ["authority_impersonation", "threat", "urgency", "gift_card_payment"],
        "lures": ["tax_fraud", "arrest_warrant"],
        "channels": ["voice", "sms"],
        "guidance": {
            "do_now": ["Hang up immediately. The IRS does not call demanding immediate payment via gift cards or wire transfer."],
            "report_to": ["Report to the Treasury Inspector General for Tax Administration (TIGTA)."],
            "recovery": ["If you paid, contact the gift card issuer or your bank immediately."]
        },
        "indicators": [
            {"value": "1-800-555-0199", "kind": "phone"},
            {"value": "1-888-555-0102", "kind": "phone"}
        ],
        "templates": [
            "This is the IRS. There is a warrant out for your arrest due to unpaid taxes. Call 1-800-555-0199 immediately.",
            "Final Notice from Internal Revenue Service. We are filing a lawsuit against you. Contact 1-888-555-0102."
        ]
    },
    {
        "name": "tech_support_refund",
        "summary": "Fake Geek Squad or Norton renewal emails charging a massive fee, prompting the victim to call to cancel.",
        "tactics": ["brand_impersonation", "refund_scam", "remote_access"],
        "lures": ["subscription_renewal", "accidental_charge"],
        "channels": ["email"],
        "guidance": {
            "do_now": ["Do not call the number in the email. Do not allow them remote access to your computer."],
            "report_to": ["Forward to the FTC or ActionFraud."],
            "recovery": ["If they accessed your PC, disconnect it from the internet and run a malware scan. Contact your bank."]
        },
        "indicators": [
            {"value": "1-800-555-0188", "kind": "phone"},
            {"value": "billing@geeksquad-renewals.net", "kind": "email"}
        ],
        "templates": [
            "Geek Squad Auto-Renewal: Your account has been charged $399.99 for a 1-year subscription. If you did not authorize this, call 1-800-555-0188 to cancel.",
            "Norton LifeLock: Invoice #99812. $450 has been deducted from your account. Call support to dispute this charge."
        ]
    }
]

def seed():
    print("Initializing Database...")
    store.init_db(Path(".antibody_data"))
    
    # Generate 5 fake power users for the leaderboard
    power_users = [ingest.anon_reporter(uuid.uuid4().hex) for _ in range(5)]
    
    # 1. Insert Families and Indicators
    for fam in FAMILIES:
        store.upsert_family(
            name=fam["name"],
            summary=fam["summary"],
            tactics=fam["tactics"],
            lures=fam["lures"],
            channels=fam["channels"],
            seen_at=_hours_ago(72) # Emerged 3 days ago
        )
        store.set_guidance(
            family_name=fam["name"],
            do_now=fam["guidance"]["do_now"],
            report_to=fam["guidance"]["report_to"],
            recovery=fam["guidance"]["recovery"]
        )
        for ind in fam["indicators"]:
            store.upsert_indicator(value=ind["value"], kind=ind["kind"], family_name=fam["name"])
            
    # 2. Insert Fake Reports (Seed the Feed and Leaderboard)
    print("Seeding reports...")
    for _ in range(40):
        fam = random.choice(FAMILIES)
        text = random.choice(fam["templates"])
        channel = random.choice(fam["channels"])
        reporter = random.choice(power_users + [None, None]) # Sometimes anonymous
        
        # Stagger reports over the last 48 hours
        hrs_ago = random.uniform(0.1, 48.0)
        
        # Fake verdict
        verdict = {
            "band": "scam",
            "band_label": "High Risk",
            "band_emoji": "🔴",
            "confidence": 0.95,
            "family": fam["name"],
            "family_display": fam["name"].replace("_", " ").title(),
            "report_count": store.family_report_count(fam["name"]) + 1,
            "reasons": ["Matches known tactics and lures.", "Matches known indicators."],
            "signals": {"indicator": 1.0, "semantic": 0.9, "structural": 0.8},
            "indicators": fam["indicators"],
            "tactics": fam["tactics"],
            "lures": fam["lures"],
            "guidance": fam["guidance"],
            "transcript": text,
            "input_kind": "text"
        }
        
        rid = _fake_report_id()
        
        store.add_report(
            report_id=rid,
            normalized_text=text,
            channel=channel,
            family_name=fam["name"],
            reporter_id=reporter,
            indicators=fam["indicators"],
            tactics=fam["tactics"],
            lures=fam["lures"],
            outcome="confirmed_scam" if reporter else None, # Verified if logged in
            reported_at=_hours_ago(hrs_ago),
            verdict_json=json.dumps(verdict)
        )
        
        if reporter:
            store.bump_trust(reporter, 0.1)

    print(f"Successfully seeded database with {len(FAMILIES)} families and 40 reports.")
    print("You can view the rich Graph, Feed, and Leaderboard in the UI immediately!")

if __name__ == "__main__":
    seed()
